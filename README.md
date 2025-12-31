# Majik Blender Edu

**Majik Blender Edu** is a **submission integrity and student activity tracking addon for Blender** designed to help educators verify a student's work. It records Blender-specific actions such as editing meshes, adding modifiers, importing assets, and scene statistics (vertices, faces, etc.), ensuring that submitted projects are authentic and untampered.  

This addon leverages **Blender's native Python API** for precise action logging and the **cryptography library** ([pyca/cryptography](https://github.com/pyca/cryptography), [cryptography.io](https://cryptography.io/)) for secure storage. Logs are encrypted with **AES Fernet**, and only the teacher with the correct key can decrypt them.  



- [Majik Blender Edu](#majik-blender-edu)
  - [Key Features](#key-features)
  - [Technical Overview](#technical-overview)
  - [Installation](#installation)
    - [Option 1: Install from Prebuilt ZIP (Recommended)](#option-1-install-from-prebuilt-zip-recommended)
    - [Option 2: Build from Source (Advanced / Developers)](#option-2-build-from-source-advanced--developers)
    - [More Information](#more-information)
  - [How to Use](#how-to-use)
    - [For Teachers](#for-teachers)
    - [For Students](#for-students)
  - [Majik Blender Edu Analyzer](#majik-blender-edu-analyzer)
    - [How to Use the Analyzer](#how-to-use-the-analyzer)
    - [Understanding the Dashboard](#understanding-the-dashboard)
      - [**1. Overview KPIs**](#1-overview-kpis)
      - [**2. Visual Charts**](#2-visual-charts)
      - [**3. Action Logs**](#3-action-logs)
    - [How the Numbers Work](#how-the-numbers-work)
    - [Integration \& SDK](#integration--sdk)
  - [Contributing](#contributing)
  - [Notes](#notes)
  - [License](#license)
    - [1. Blender Addon (Teacher \& Student Versions)](#1-blender-addon-teacher--student-versions)
    - [2. Majik Blender Edu Analyzer \& SDK](#2-majik-blender-edu-analyzer--sdk)
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

Majik Blender Edu can be installed either by downloading a prebuilt extension package or by building the extension directly from the source code.

### Option 1: Install from Prebuilt ZIP (Recommended)

1. Download the `.zip` file.
   - For Teachers ([Download Majik Blender Edu – Teacher](https://extensions.blender.org/approval-queue/majik-blender-edu-teacher))
   - For Students ([Download Majik Blender Edu – Students](https://extensions.blender.org/approval-queue/majik-blender-edu-students))
2. Open **Blender > Edit > Preferences > Extensions > Install from Disk**.  
3. Enable **Majik Blender Edu**.  

### Option 2: Build from Source (Advanced / Developers)

You may also install Majik Blender Edu by cloning or downloading the GitHub repository and building the extension ZIP yourself using Blender’s command-line extension builder.

1. Clone or download the repository:
```bash

git clone https://github.com/your-org/majik-blender-edu.git

```
> (Or download the ZIP from GitHub and extract it.)


2. Run the following command to build the extension ZIP:

```bash

& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" `
  --background `
  --factory-startup `
  --command extension build `
  --source-dir "C:\majik-blender-edu\majik_blender_edu_students" `
  --output-dir "C:\majik-blender-edu\dist\students" `
  --split-platforms `
  --verbose

```

```bash

& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" `
  --background `
  --factory-startup `
  --command extension build `
  --source-dir "C:\majik-blender-edu\majik_blender_edu_teacher" `
  --output-dir "C:\majik-blender-edu\dist\teacher" `
  --split-platforms `
  --verbose

```

3. Once built, locate the generated `.zip` file in the output directory.
3. Open **Blender > Edit > Preferences > Extensions > Install from Disk**.  
4. Enable **Majik Blender Edu**.  

### More Information

For full details on Blender’s extension build system and available command-line options, see the official documentation:

[https://docs.blender.org/manual/en/dev/advanced/command_line/extension_arguments.html#command-line-args-extension-build](https://docs.blender.org/manual/en/dev/advanced/command_line/extension_arguments.html#command-line-args-extension-build)
   
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

## Majik Blender Edu Analyzer

The **Majik Blender Edu Analyzer** is your student activity insight tool. It helps teachers assess submission authenticity, workflow efficiency, and originality by processing the encrypted logs generated by the Blender addon.

### How to Use the Analyzer

1.  **Export Action Log JSON:** From the Teacher version of the Blender addon, decrypt the project and export the action log JSON.
2.  **Upload to Analyzer:** Go to [Majik Blender Edu Analyzer](https://thezelijah.world/tools/education-majik-blender-edu) and upload the JSON file.
3.  **Provide Teacher Key:** Enter your AES key manually or import your key JSON to decrypt the logs.
4.  **Enter Student ID:** Use the identifier you assigned in Blender to match the logs.
5.  **Analyze:** The dashboard will generate KPIs, metrics, charts, and detailed logs for analysis.

### Understanding the Dashboard

The dashboard is divided into several key areas to provide a comprehensive view of student behavior:

#### **1. Overview KPIs**
| KPI                    | Description                                                          | Example / Notes                |
| :--------------------- | :------------------------------------------------------------------- | :----------------------------- |
| **Integrity Status**   | Validates whether the action logs have been tampered with.           | VALID / TAMPERED               |
| **Total Working Time** | Total duration of the student’s active Blender session.              | 2h 15m                         |
| **Effective Time**     | Time spent actively performing actions (mesh edits, modifiers, etc.) | 1h 50m                         |
| **Total Logs**         | Number of individual actions logged during the session.              | 245 logs                       |
| **Authenticity Score** | Evaluates originality and potential issues in the workflow.          | 92/100                         |
| **Scene Complexity**   | Summary of total vertices and object count.                          | Vertices: 34,500 / Objects: 45 |
| **Most Active Object** | The object where the student performed the most actions.             | Cube.001                       |
| **Idle Ratio**         | Percentage of time spent without performing any actions.             | 15%                            |
| **Entropy Score**      | Measures workflow irregularity or randomness in actions.             | 1.42                           |

#### **2. Visual Charts**
| Chart                 | Description                                       | Insights                                        |
| :-------------------- | :------------------------------------------------ | :---------------------------------------------- |
| **Scene Growth**      | Tracks vertices and objects over time.            | Shows how quickly the scene was built.          |
| **Action Density**    | Number of actions performed per minute.           | Identifies bursts of activity vs. idle periods. |
| **Type Distribution** | Pie chart of mesh edits, modifiers, imports, etc. | Shows which tasks dominated the session.        |
| **Entropy Trend**     | Measures workflow irregularity over time.         | Spikes may indicate unusual behavior or jumps.  |
| **Idle Periods**      | Timeline of exact periods of inactivity.          | Useful for identifying distractions or breaks.  |

#### **3. Action Logs**
A chronological detailed view of every action recorded, including mesh edits, modifier applications, imports/exports, and scene statistics changes.

### How the Numbers Work

The Analyzer aggregates data through several layers to ensure reliability:
* **Blockchain-style Verification:** Hashing ensures logs haven't been edited post-export.
* **KPI Computation:** Calculates "Effective Time" by filtering out periods of inactivity.
* **Trend Analysis:** Uses Plotly to visualize temporal trends like scene growth and action entropy.
* **Reactive Updates:** KPIs and charts refresh immediately upon importing a new JSON.

> **💡 Teacher Tip:** Focus on the **Authenticity Score** and **Entropy Trends** to detect irregular workflows or potentially copied content.

### Integration & SDK

Majik Blender Edu is designed to be flexible. You can integrate it into your own web projects or custom automated grading systems.

| Integration Type  | Description                                              | Link                                                                                                           |
| :---------------- | :------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| **Teacher Addon** | Encrypt and validate student sessions.                   | [Download](https://extensions.blender.org/approval-queue/majik-blender-edu-teacher)                            |
| **Student Addon** | Log actions for submission.                              | [Download](https://extensions.blender.org/approval-queue/majik-blender-edu-students)                           |
| **Analyzer SDK**  | TypeScript/NPM package to process logs programmatically. | [@thezelijah/majik-blender-edu-analyzer](https://www.npmjs.com/package/@thezelijah/majik-blender-edu-analyzer) |
| **Source Code**   | Full source, issues, and contribution guide.             | [GitHub Repo](https://github.com/jedlsf/majik-blender-edu)                                                     |

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

This project uses a **split-licensing model** to provide both community protection and developer flexibility:

### 1. Blender Addon (Teacher & Student Versions)
The Blender extensions are licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.
* You are free to use, modify, and redistribute this software.
* Any derivative works of the Blender Addon must also be distributed under the GPL-3.0-or-later.
* See the [LICENSE](LICENSE) file for full details.

> ⚠️ **Note for educators and institutions:** If you modify and redistribute the Blender addon (internally or externally), those changes must remain open-source under the same GPL license.

### 2. Majik Blender Edu Analyzer & SDK
The Analyzer web tool and the [`@thezelijah/majik-blender-edu-analyzer`](https://www.npmjs.com/package/@thezelijah/majik-blob) NPM package are licensed under the **Apache License 2.0**.
* This is a permissive license that allows for broader integration into various software environments, including commercial and proprietary projects.
* This ensures developers can build custom dashboards or automated grading systems using our logic without GPL restrictions.
* See the `LICENSE-APACHE`(LICENSE.APACHE) file for full details (or visit the [Apache 2.0 Official Site](https://www.apache.org/licenses/LICENSE-2.0)).
---


## Author

Made with 💙 by [@thezelijah](https://github.com/jedlsf)

## About the Developer

- **Developer**: Josef Elijah Fabian
- **GitHub**: [https://github.com/jedlsf](https://github.com/jedlsf)
- **Project Repository**: [https://github.com/jedlsf/majik-blender-edu](https://github.com/jedlsf/majik-blender-edu)

---

## Contact

- **Business Email**: [business@thezelijah.world](mailto:business@thezelijah.world)
- **Official Website**: [https://www.thezelijah.world](https://www.thezelijah.world)
