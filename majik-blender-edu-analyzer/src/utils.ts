/* eslint-disable @typescript-eslint/no-explicit-any */
import crypto from "crypto";
import Fernet from "fernet";
import { ActionLogEntry, RawActionLogEntry } from "./types";
import { Buffer } from "buffer";

// ---------------------------
// UTILS
// ---------------------------

/**
 * Generates a Fernet-compatible key from a password string using PBKDF2.
 * Mirrors Python's fernet_key_from_string.
 */
export function fernetKeyFromString(password: string, salt: Buffer): string {
  const derivedKey = crypto.pbkdf2Sync(
    password,
    salt,
    390_000, // OWASP recommended iterations
    32, // 32 bytes = 256 bits
    "sha256"
  );
  return Buffer.from(derivedKey).toString("base64url"); // Fernet expects base64url
}

/**
 * SHA256 hash of a string, hex-encoded.
 */
export function sha256Hex(data: string): string {
  return crypto.createHash("sha256").update(data, "utf8").digest("hex");
}

// ---------------------------
// Low-level AES / Fernet functions
// ---------------------------

/**
 * Encrypt metadata using AES (Fernet)
 */

export function aesEncrypt(
  metadata: Record<string, any>,
  key: string,
  salt: Buffer
): string {
  const aesKey = fernetKeyFromString(key, salt);
  const secret = new Fernet.Secret(aesKey);
  const token = new Fernet.Token({ secret, time: Date.now() / 1000 });
  return token.encode(JSON.stringify(metadata));
}

/**
 * Decrypt metadata using AES (Fernet)
 */
export function aesDecrypt(
  encryptedMetadata: string,
  key: string,
  salt: Buffer
): string {
  const aesKey = fernetKeyFromString(key, salt);
  const secret = new Fernet.Secret(aesKey);
  const token = new Fernet.Token({ secret, token: encryptedMetadata, ttl: 0 }); // ttl 0 = no expiration
  return token.decode();
}

// ---------------------------
// High-level wrapper functions
// ---------------------------

/**
 * Encrypt metadata using AES (Fernet)
 */
export function encryptMetadata(
  metadata: Record<string, any>,
  key: string,
  salt: Buffer
): string {
  if (!salt || salt.length === 0) {
    throw new Error("Missing salt; cannot encrypt securely");
  }

  const hashedKey = sha256Hex(key); // mirror Python logic
  return aesEncrypt(metadata, hashedKey, salt);
}

/**
 * Decrypt metadata using AES (Fernet)
 */
export function decryptMetadata(
  encryptedMetadata: string,
  key: string,
  salt: Buffer
): Record<string, any> {
  if (!salt || salt.length === 0) {
    throw new Error("Missing salt; cannot decrypt securely");
  }

  const hashedKey = sha256Hex(key); // mirror Python logic
  const decrypted = aesDecrypt(encryptedMetadata, hashedKey, salt);
  return JSON.parse(decrypted);
}

function deepSortKeys(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(deepSortKeys);
  } else if (obj && typeof obj === "object") {
    return Object.keys(obj)
      .sort()
      .reduce((acc: any, key) => {
        acc[key] = deepSortKeys(obj[key]);
        return acc;
      }, {});
  }
  return obj;
}



export function computeEntryHash(entry: RawActionLogEntry): string {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { ph, ...rest } = entry;

  const canonicalObj = deepSortKeys(rest);
  let canonical = JSON.stringify(canonicalObj);

  // Patch "dt":0 to "dt":0.0 in the JSON string only
  canonical = canonical.replace(/"dt":0(,|})/g, '"dt":0.0$1');

  return sha256Hex(canonical);
}

export function generateGenesisKey(
  teacherKey: string,
  studentId: string
): string {
  const combined = `${teacherKey}:${studentId}`;
  const combinedB64 = Buffer.from(combined, "utf-8").toString("base64");
  return sha256Hex(combinedB64);
}

export function validateGenesisKey(
  current: string,
  teacherKey: string,
  studentId: string
): boolean {
  return current === generateGenesisKey(teacherKey, studentId);
}

export function validateLogIntegrity(
  rawLogs: RawActionLogEntry[],
  teacherKey: string,
  studentId: string
): boolean {
  if (!rawLogs.length) return true;

  const logs = rawLogs;

  const genesis = logs[0];
  const expectedGenesis = generateGenesisKey(teacherKey, studentId);

  if (genesis.ph !== expectedGenesis) {
    console.warn("Genesis key mismatch!");
    return false;
  }
  console.log("Genesis key matched ✅");

  for (let i = 1; i < logs.length; i++) {
    const entry = logs[i];
    const expectedPrev = computeEntryHash(logs[i - 1]);

    if (entry.ph !== expectedPrev) {
      console.warn("Hash mismatch at index", i);
      return false;
    }
  }

  return true;
}


/**
 * Calculates elapsed time in seconds between two log entries.
 * Returns 0 if previous entry is missing or timestamps are invalid.
 */
export function calculateDuration(
  previousEntry?: ActionLogEntry,
  currentEntry?: ActionLogEntry
): number {
  if (!previousEntry || !currentEntry) return 0;

  const prevTime = new Date(previousEntry.timestamp).getTime();
  const currTime = new Date(currentEntry.timestamp).getTime();

  if (!Number.isFinite(prevTime) || !Number.isFinite(currTime)) return 0;

  const diff = (currTime - prevTime) / 1000;

  // Never allow negative or NaN durations
  return diff > 0 ? Math.round(diff) : 0;
}

export function isSessionStartLog(entry: ActionLogEntry): boolean {
  return (
    entry.actionType === "Session Started" &&
    entry.name === "__SESSION__" &&
    entry.type === "SYSTEM"
  );
}