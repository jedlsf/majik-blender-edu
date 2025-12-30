# Majik Blender Edu

**Majik Blender Edu** is a **submission integrity and student activity tracking addon for Blender** designed to help educators verify a student's work. It records Blender-specific actions such as editing meshes, adding modifiers, importing assets, and scene statistics (vertices, faces, etc.), ensuring that submitted projects are authentic and untampered.  

This addon leverages **Blender's native Python API** for precise action logging and the **cryptography library** ([pyca/cryptography](https://github.com/pyca/cryptography), [cryptography.io](https://cryptography.io/)) for secure storage. Logs are encrypted with **AES Fernet**, and only the teacher with the correct key can decrypt them.  



- [Majik Blender Edu](#majik-blender-edu)
  - [Key Features](#key-features)
  - [Technical Overview](#technical-overview)
  - [Installation](#installation)
  - [How to Use](#how-to-use)
    - [For Teachers](#for-teachers)
    - [For Students](#for-students)
  - [Contributing](#contributing)
  - [Notes](#notes)
  - [License](#license)
  - [Author](#author)
  - [About the Developer](#about-the-developer)
  - [Contact](#contact)

---

## Key Features

- **Action Logging:** Tracks all essential Blender operations including mesh edits, modifiers, imports, and scene statistics.  
- **Blockchain-style Log Integrity:** Each log entry contains a hash of the previous entry, forming a chain that guarantees log authenticity.  
- **Secure Encryption:** Uses AES Fernet to encrypt logs; decryption is only possible with the teacher’s key.  
- **Teacher Verification:** Teachers can decrypt, validate, and export logs to JSON for deeper analysis.  
- **Student Timer & Visual Feedback:** Tracks session times and overlays a red rectangle in the viewport to indicate an active logging session.  
- **Cross-project Key Reuse:** Teachers can reuse a key across multiple projects while keeping logs secure.  
- **Reset Functionality:** Teachers can reset a project, removing all prior logs and settings.  

---

## Technical Overview

- **Platform Tested:** Blender 5 on Windows  
- **Python Libraries:**  
  - `cryptography` (AES Fernet encryption)  
  - Blender Python API (native)  
- **Log Structure:** Each log is chained via hash references, similar to blockchain, making tampering evident.  
- **Performance:** Optimized for projects up to ~60k vertices; higher complexity projects are untested.  
- **Security:** Logs cannot be decrypted or altered without the teacher’s key.  

> ⚠️ **Note:** Ensure the cryptography library is installed; it’s a mandatory dependency. Other Blender versions and platforms are planned for future support.  

---

## Installation

1. Download the `.zip` file.  
2. Open **Blender > Preferences > Add-ons > Install**.  
3. Enable **Majik Blender Edu**.  

---

## How to Use

### For Teachers

**A. Encryption and Preparing a Project**
1. Open Blender and access **Majik Blender Edu** in **Scene Properties**.  
2. Enter a key manually or generate a random one.  
3. Download and securely store your key. **Keep this private**—it unlocks all logs.  
4. Enter the student’s ID, email, or any identifier.  
5. Click **Encrypt & Apply Signature**. This marks the project as teacher-signed. Students can now begin their session.  

**B. Decryption and Validation**
1. Open the submitted project in Blender.  
2. Navigate to the **Decrypt** tab in Scene Properties.  
3. Import or enter your key.  
4. Click **Decrypt & Validate**. Depending on project complexity, this may take some time.  
5. If valid, a banner will confirm log integrity and display the timestamp of signing.  
6. Optionally, download the action logs as JSON for deeper analysis.  
7. Upload the JSON to [Majik Blender Edu Analyzer](https://thezelijah.world/tools/education-majik-blender-edu) for insights.  

**C. Resetting a Project**
1. Decrypt and validate the project first.  
2. The **Reset Key** button will appear.  
3. Click it to remove all existing logs and settings. **Warning:** This action is irreversible.  

---

### For Students

1. Open Blender and access **Majik Blender Edu** in **Scene Properties**.  
2. Always **start the timer** before working; logging only records active sessions.  
3. A red rectangle in the viewport signals an active session.  
4. Stop the timer once finished to save logs. Manual saves (Ctrl+S) also store log progress.  
5. Submit the `.blend` file to your teacher.  
6. Optionally, download encrypted logs as a backup (decrypted logs require the teacher’s key).  

---

## Contributing

If you want to contribute or help extend support to more Blender versions and platforms, reach out via email. All contributions are welcome!  

---

## Notes

- Currently only tested on **Blender 5 on Windows**.  
- Works reliably with light to medium projects (~60k vertices).  
- No stress testing performed yet; report any issues in the comments.  
- Ensure secure handling of your encryption key; unauthorized access compromises log integrity.  

---

## License

This project is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.

You are free to use, modify, and redistribute this software under the terms of the GPL.
Any derivative works must also be distributed under the same license.

See the [LICENSE](LICENSE) file for full details.

> ⚠️ Note for educators and institutions  
> This software is open-source under GPL-3.0-or-later.  
> If you modify and redistribute it (internally or externally), those changes must also be shared under the same license.

---

## Author

Made with 💙 by [@thezelijah](https://github.com/jedlsf)

## About the Developer

- **Developer**: Josef Elijah Fabian
- **GitHub**: [https://github.com/jedlsf](https://github.com/jedlsf)
- **Project Repository**: [https://github.com/jedlsf/majik-runway](https://github.com/jedlsf/majik-runway)

---

## Contact

- **Business Email**: [business@thezelijah.world](mailto:business@thezelijah.world)
- **Official Website**: [https://www.thezelijah.world](https://www.thezelijah.world)
