# Majik Blender Edu

**Majik Blender Edu** is a **submission integrity and student activity tracking addon for Blender** designed to help educators verify a student's work. It records Blender-specific actions such as editing meshes, adding modifiers, importing assets, and scene statistics (vertices, faces, etc.), ensuring that submitted projects are authentic and untampered.  

This addon leverages **Blender's native Python API** for precise action logging and the **cryptography library** ([pyca/cryptography](https://github.com/pyca/cryptography), [cryptography.io](https://cryptography.io/)) for secure storage. Logs are encrypted with **AES Fernet**, and only the teacher with the correct key can decrypt them.  

![WA_Tools_Security_MajikBlenderEdu](https://github.com/user-attachments/assets/5286c8b9-e230-4fbd-a77c-777347568b7d)

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
    - [Installation](#installation-1)
    - [Quick Start](#quick-start)
    - [Example Usage](#example-usage)
    - [API Reference](#api-reference)
      - [`MajikBlenderEdu` Class](#majikblenderedu-class)
        - [1. Initialization \& Parsing](#1-initialization--parsing)
        - [2. Integrity \& Validation](#2-integrity--validation)
        - [3. Time \& Session Metrics](#3-time--session-metrics)
        - [4. Scene \& Modeling Metrics](#4-scene--modeling-metrics)
        - [5. Behavioral Analysis](#5-behavioral-analysis)
        - [6. Scoring \& Verdicts](#6-scoring--verdicts)
        - [7. Charts \& Visualization (Plotly Data)](#7-charts--visualization-plotly-data)
        - [8. Export \& Serialization](#8-export--serialization)
      - [Types](#types)
      - [Utils / Functions](#utils--functions)
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

Majik Blender Edu is a Blender addon for verifying student work. Both teacher and student workflows are now consolidated into a single addon. A User Mode selector in the Scene Properties lets you switch between Teacher or Student mode. By default, it opens in Teacher mode.

### Option 1: Install from Prebuilt ZIP (Recommended)

1. Download the `.zip` file.
   - ([Download Majik Blender Edu](https://extensions.blender.org/approval-queue/majik-blender-edu-teacher)) (single addon, all modes included)
2. Open **Blender > Edit > Preferences > Extensions > Install from Disk**.  
3. Enable **Majik Blender Edu**.

<img width="869" height="504" alt="image" src="https://github.com/user-attachments/assets/7f82868f-1724-4b7c-a80a-60e97c0e5869" />


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

<img width="361" height="305" alt="image" src="https://github.com/user-attachments/assets/1c43b1cf-a175-46ee-a2b3-91666b80fd77" />

1. Open Blender and access **Majik Blender Edu** in **Scene Properties**. Select **Teacher** as your User Mode from the **Mode Selector**.
2. Enter a key manually or generate a random one.  
3. Download and securely store your key. **Keep this private**—it unlocks all logs.  
4. Enter the student’s ID, email, or any identifier.  
5. Click **Encrypt & Apply Signature**. This marks the project as teacher-signed. Students can now begin their session.  

**B. Decryption and Validation**

<img width="364" height="446" alt="image" src="https://github.com/user-attachments/assets/90aa686a-cccb-4861-b31c-490a7102617d" />

1. Open the submitted project in Blender.  
2. Navigate to the **Decrypt** tab in Scene Properties.  
3. Import or enter your key.  
4. Click **Decrypt & Validate**. Depending on project complexity, this may take some time.  
5. If valid, a banner will confirm log integrity and display the timestamp of signing.  
6. Optionally, download the action logs as JSON for deeper analysis.  
7. Upload the JSON to [Majik Blender Edu Analyzer](https://thezelijah.world/tools/education-majik-blender-edu) for insights.  

**C. Resetting a Project**

<img width="342" height="143" alt="image" src="https://github.com/user-attachments/assets/3ca7e8b3-02d7-4803-a8fa-43de595e4c1a" />


1. Decrypt and validate the project first.  
2. The **Reset Key** button will appear.  
3. Click it to remove all existing logs and settings. **Warning:** This action is irreversible.  

---

### For Students

<img width="347" height="237" alt="image" src="https://github.com/user-attachments/assets/99721e6f-7afe-491f-91c3-83b68d076dd6" />


1. Open Blender and access **Majik Blender Edu** in **Scene Properties**. Select **Student** as your User Mode from the **Mode Selector**.
2. Always **start the timer** before working; logging only records active sessions.  
3. A red rectangle in the viewport signals an active session.  
4. Stop the timer once finished to save logs. Manual saves (Ctrl+S) also store log progress.  
5. Submit the `.blend` file to your teacher.  
6. Optionally, download encrypted logs as a backup (decrypted logs require the teacher’s key).  

---

## Majik Blender Edu Analyzer

The **Majik Blender Edu Analyzer** is your student activity insight tool. It helps teachers assess submission authenticity, workflow efficiency, and originality by processing the encrypted logs generated by the Blender addon.

<img width="1880" height="903" alt="image" src="https://github.com/user-attachments/assets/e02a5d04-d97a-4b46-a45f-5094be0093ac" />


### How to Use the Analyzer

1.  **Export Action Log JSON:** From the Teacher version of the Blender addon, decrypt the project and export the action log JSON.
2.  **Upload to Analyzer:** Go to [Majik Blender Edu Analyzer](https://thezelijah.world/tools/education-majik-blender-edu) and upload the JSON file.
3.  **Provide Teacher Key:** Enter your AES key manually or import your key JSON to decrypt the logs.
4.  **Enter Student ID:** Use the identifier you assigned in Blender to match the logs.
5.  **Analyze:** The dashboard will generate KPIs, metrics, charts, and detailed logs for analysis.

<img width="1139" height="876" alt="image" src="https://github.com/user-attachments/assets/45d88fd2-2155-4ee0-bdce-e775cf3bf58e" />


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

<img width="1697" height="913" alt="image" src="https://github.com/user-attachments/assets/fb41b026-2e63-4b7b-a75d-356159a4fa82" />


#### **3. Action Logs**
A chronological detailed view of every action recorded, including mesh edits, modifier applications, imports/exports, and scene statistics changes.

<img width="1900" height="915" alt="image" src="https://github.com/user-attachments/assets/64457736-ef21-41d8-9d5d-35e60f4ee6c2" />


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


### Installation

```bash
npm install @thezelijah/majik-blender-edu-analyzer
```

---


### Quick Start

```ts
import { MajikBlenderEdu } from "@thezelijah/majik-blender-edu-analyzer";

const edu = MajikBlenderEdu.initialize(
  decryptedActionLogJSON,
  teacherAESKey,
  studentId
);

const summary = edu.getSummary();
console.log(summary.score, summary.verdict);
```

---


### Example Usage

```tsx
"use client";

import React, { useMemo, useState } from "react";
import styled from "styled-components";
import {
  GearIcon,
  InfoIcon,
  LogIcon,
  ShieldCheckIcon,
  ClockIcon,
  RocketIcon,
  NotebookIcon,
  StarIcon,
  SquaresFourIcon,
  CubeIcon,
  LightningIcon,
  HourglassIcon,
  FunnelIcon,
} from "@phosphor-icons/react";
import DynamicPagedTab, {
  TabContent,
} from "@/components/functional/DynamicPagedTab";

import { formatPercentage, formatTime } from "@/utils/helper";

import { DynamicColoredValue } from "@/components/foundations/DynamicColoredValue";
import theme from "@/globals/theme";

import { MajikBlenderEdu } from "@/SDK/tools/education/majik-blender-edu/majik-blender-edu";
import MajikBlenderEduHealthIndicator from "./MajikBlenderEduHealthIndicator";
import SetupMajikBlenderEdu from "./SetupMajikBlenderEdu";
import ActionLogViewer from "./ActionLogViewer";
import PlotlyTrendChart from "@/components/plotly/PlotlyTrendChart";
import PlotlyPieChart from "@/components/plotly/PlotlyPieChart";

// ======== Styled Components ========
const RootContainer = styled.div`
//css
`;

const HeaderCards = styled.div`
//css
`;

const TopHeaderRow = styled.div`
//css
`;

const Card = styled.div`
//css
`;

const CardTitle = styled.div`
//css
`;

const CardValue = styled.div`
//css
`;

const CardSubtext = styled.div`
//css
`;

const MainGrid = styled.div`
//css
`;

const ChartPlaceholder = styled.div`
//css
`;

interface DashboardMajikBlenderEduProps {
  instance: MajikBlenderEdu;
  onUpdate?: (updatedInstance: MajikBlenderEdu) => void;
}

// ======== Main Component ========

const DashboardMajikBlenderEdu: React.FC<DashboardMajikBlenderEduProps> = ({
  instance,
}) => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const dashboardSnapshot = useMemo(
    () => instance.getSummary(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const health = useMemo(
    () => instance.getEduHealth(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const integrityStatus = useMemo(
    () => instance.validateLogChain(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartSceneGrowthOverTime = useMemo(
    () => instance.getPlotlySceneGrowthOverTime(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartActionDensity = useMemo(
    () => instance.getPlotlyActionDensity(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartActionTypePie = useMemo(
    () => instance.getPlotlyActionTypePie(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartAuthenticityScorePie = useMemo(
    () => instance.getPlotlyAuthenticityScorePie(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartEntropyTrend = useMemo(
    () => instance.getPlotlyEntropyTrend(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const chartIdleTimeTraces = useMemo(
    () => instance.getPlotlyIdleTimeTraces(),

    // eslint-disable-next-line react-hooks/exhaustive-deps
    [instance, refreshKey]
  );

  const InformationTabs: TabContent[] = [
    {
      id: "info-overview",
      name: "Overview",
      icon: InfoIcon,
      content: (
        <>
          <TopHeaderRow>
            <MajikBlenderEduHealthIndicator health={health} />
          </TopHeaderRow>

          {/* ===== Header / KPI Cards ===== */}
          <HeaderCards>
            <Card>
              <CardTitle>
                <ShieldCheckIcon size={20} /> Integrity Status
              </CardTitle>
              <CardValue>{integrityStatus ? "VALID" : "TAMPERED"}</CardValue>
              <CardSubtext>{!!dashboardSnapshot.flags.join(", ")}</CardSubtext>
            </Card>
            <Card>
              <CardTitle>
                <ClockIcon size={20} />
                Total Working Time
              </CardTitle>
              <CardValue>
                {formatTime(
                  dashboardSnapshot.totalWorkingTime,
                  "seconds",
                  undefined,
                  true,
                  "duration"
                )}
              </CardValue>
            </Card>

            <Card>
              <CardTitle>
                <RocketIcon size={20} />
                Effective Time
              </CardTitle>
              <CardValue>
                {formatTime(
                  dashboardSnapshot.effectiveTime,
                  "seconds",
                  undefined,
                  true,
                  "duration"
                )}
              </CardValue>
            </Card>

            <Card>
              <CardTitle>
                <NotebookIcon size={20} /> Total Logs
              </CardTitle>
              <CardValue>
                {dashboardSnapshot.totalLogs.toLocaleString()}
              </CardValue>
            </Card>

            <Card>
              <CardTitle>
                <StarIcon size={20} /> Authenticity Score
              </CardTitle>
              <CardValue>
                <DynamicColoredValue
                  value={dashboardSnapshot.score} // numeric months remaining
                  colorsMap={[
                    { color: theme.colors.error, max: 59.99 },
                    { color: theme.colors.brand.white, min: 60, max: 84.99 },
                    { color: theme.colors.brand.green, min: 85 },
                  ]}
                  size={28}
                  weight={700}
                >
                  {dashboardSnapshot.score}/100
                </DynamicColoredValue>
              </CardValue>
            </Card>
          </HeaderCards>

          {/* ===== SubHeader / Secondary KPI Cards ===== */}
          <HeaderCards>
            <Card>
              <CardTitle>
                <SquaresFourIcon size={20} /> Total Vertices
              </CardTitle>
              <CardValue>
                {dashboardSnapshot.totalVertices.toLocaleString()}
              </CardValue>
            </Card>
            <Card>
              <CardTitle>
                <CubeIcon size={20} /> Total Objects
              </CardTitle>
              <CardValue>
                {dashboardSnapshot.totalObjects.toLocaleString()}
              </CardValue>
            </Card>
            <Card>
              <CardTitle>
                <LightningIcon size={20} /> Most Active Object
              </CardTitle>
              <CardValue>{dashboardSnapshot.mostActiveObject}</CardValue>
            </Card>

            <Card>
              <CardTitle>
                <HourglassIcon size={20} />
                Idle Ratio
              </CardTitle>
              <CardValue>
                <DynamicColoredValue
                  value={dashboardSnapshot.idleRatio ?? 0}
                  colorsMap={[
                    { color: theme.colors.brand.green, max: 0.299 },
                    { color: theme.colors.brand.white, min: 0.3, max: 0.799 },
                    { color: theme.colors.error, min: 0.8 },
                  ]}
                  size={28}
                  weight={700}
                >
                  {formatPercentage(dashboardSnapshot.idleRatio ?? 0, true)}
                </DynamicColoredValue>
              </CardValue>
            </Card>
            <Card>
              <CardTitle>
                <FunnelIcon size={20} />
                Entropy Score
              </CardTitle>
              <CardValue>
                <DynamicColoredValue
                  value={dashboardSnapshot.entropyScore ?? 0}
                  colorsMap={[
                    { color: theme.colors.error, max: 1.299 },
                    { color: theme.colors.brand.white, min: 1.3, max: 1.499 },
                    { color: theme.colors.brand.green, min: 1.5 },
                  ]}
                  size={28}
                  weight={700}
                >
                  {formatPercentage(dashboardSnapshot.entropyScore ?? 0, true)}
                </DynamicColoredValue>
              </CardValue>
            </Card>
          </HeaderCards>

          {/* ===== Main Grid / Charts ===== */}
          <MainGrid>
            <ChartPlaceholder>
              <PlotlyTrendChart
                data={chartSceneGrowthOverTime}
                text={{
                  title: "Scene Growth Over Time",
                  x: {
                    text: "Time",
                    format: "%H:%M:%S", // or "%b %d %H:%M" if date-based
                  },
                  y: {
                    text: "Scene Complexity",
                    suffix: "", // no unit, just counts
                  },
                }}
                disableDragZoom={false}
              />
            </ChartPlaceholder>
            <ChartPlaceholder>
              <PlotlyTrendChart
                data={chartActionDensity}
                text={{
                  title: "Action Density Over Time",
                  x: {
                    text: "Time (per minute)",
                    format: "%H:%M",
                  },
                  y: {
                    text: "Actions per Minute",
                  },
                }}
                disableDragZoom={false}
              />
            </ChartPlaceholder>
            <ChartPlaceholder>
              <PlotlyPieChart
                data={chartActionTypePie}
                title="Distribution of Actions by Type"
              />
            </ChartPlaceholder>

            <ChartPlaceholder>
              <PlotlyPieChart
                data={chartAuthenticityScorePie}
                title="Authenticity Score vs Potential Issues"
              />
            </ChartPlaceholder>
            <ChartPlaceholder>
              <PlotlyTrendChart
                data={chartEntropyTrend}
                text={{
                  title: "Action Entropy Over Time",
                  x: {
                    text: "Time",
                    format: "%H:%M:%S", // or "%b %d %H:%M" for multi-day sessions
                  },
                  y: {
                    text: "Action Entropy",
                  },
                }}
                disableDragZoom={false}
                smooth={false}
              />
            </ChartPlaceholder>

            <ChartPlaceholder>
              <PlotlyTrendChart
                data={chartIdleTimeTraces}
                text={{
                  title: "Idle Periods Over Time",
                  x: {
                    text: "Time",
                    format: "%H:%M:%S", // or "%b %d %H:%M" for long sessions
                  },
                  y: {
                    text: "Idle Time",
                    suffix: " sec",
                  },
                }}
                disableDragZoom={false}
                smooth={false}
              />
            </ChartPlaceholder>
          </MainGrid>
        </>
      ),
    },

    {
      id: "info-logs",
      name: "Action Logs",
      icon: LogIcon,
      content: (
        <>
          <ActionLogViewer instance={instance} />
        </>
      ),
    },

    {
      id: "info-settings",
      name: "Settings",
      icon: GearIcon,
      content: (
        <>
          <SetupMajikBlenderEdu />
        </>
      ),
    },
  ];

  return (
    <RootContainer>
      {/* ===== Tabs ===== */}

      <DynamicPagedTab tabs={InformationTabs} position="left" />
    </RootContainer>
  );
};

export default DashboardMajikBlenderEdu;

```


---

### API Reference

---


#### `MajikBlenderEdu` Class


##### 1. Initialization & Parsing

| Method                                                            | Inputs / Parameters                                                                                                  | Return Type                | Description / Purpose                                                                                            |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `initialize(json: object, teacherKey: string, studentId: string)` | `json` – decrypted action log JSON<br>`teacherKey` – AES key used for decryption<br>`studentId` – student identifier | `MajikBlenderEdu` instance | Constructs and validates a new Analyzer instance from decrypted logs. Prepares KPIs, charts, and internal state. |
| `parseFromJSON(json: object)`                                     | `json` – previously serialized Analyzer state                                                                        | `MajikBlenderEdu` instance | Reconstructs a full Analyzer instance from serialized state (for batch processing or replay).                    |

---

##### 2. Integrity & Validation

| Method                        | Inputs / Parameters | Return Type | Description / Purpose                                                                                          |
| ----------------------------- | ------------------- | ----------- | -------------------------------------------------------------------------------------------------------------- |
| `validateGenesis()`           | None                | `boolean`   | Confirms correct teacher-student binding in the logs; returns `true` if genesis entry is valid.                |
| `validateLogChain()`          | None                | `boolean`   | Verifies that the logs’ cryptographic hashes are intact and in order; returns `true` if no tampering detected. |
| `hasLogTamperingIndicators()` | None                | `boolean`   | High-level flag indicating potential log tampering, missing entries, or suspicious sequences.                  |

---

##### 3. Time & Session Metrics

| Method                               | Inputs / Parameters                                       | Return Type                             | Description / Purpose                                           |
| ------------------------------------ | --------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------- |
| `getTotalWorkingTime()`              | None                                                      | `number` (seconds)                      | Returns total session duration including idle periods.          |
| `getEffectiveWorkingTime()`          | None                                                      | `number` (seconds)                      | Returns session duration excluding idle gaps.                   |
| `getIdleRatio()`                     | None                                                      | `number` (0–1)                          | Ratio of idle time vs. total working time.                      |
| `getIdlePeriods(threshold?: number)` | `threshold` – minimum idle duration in seconds (optional) | `Array<{ start: number; end: number }>` | Returns exact timestamps of idle periods exceeding `threshold`. |

---

##### 4. Scene & Modeling Metrics

| Method                                        | Inputs / Parameters                | Return Type                                                  | Description / Purpose                                                          |
| --------------------------------------------- | ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| `getTotalVertices()`                          | None                               | `number`                                                     | Final vertex count in the scene.                                               |
| `getTotalObjects()`                           | None                               | `number`                                                     | Final object count in the scene.                                               |
| `getSceneGrowthOverTime()`                    | None                               | `Array<{ time: number; vertices: number; objects: number }>` | Timeline of scene complexity (vertices/objects) over session time.             |
| `hasMeaningfulProgress(minVertices?: number)` | `minVertices` – optional threshold | `boolean`                                                    | Checks if student made minimum modeling progress.                              |
| `detectAllImportJumps()`                      | None                               | `Array<{ time: number; importedObject: string }>`            | Detects sudden additions of objects/assets that may indicate external copying. |

---

##### 5. Behavioral Analysis

| Method                                          | Inputs / Parameters          | Return Type                                            | Description / Purpose                                                           |
| ----------------------------------------------- | ---------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------- |
| `getActionEntropy()`                            | None                         | `number`                                               | Workflow randomness metric; higher values indicate unusual or erratic patterns. |
| `getRepetitiveActionBursts(threshold?: number)` | `threshold` – actions/minute | `Array<{ start: number; end: number; count: number }>` | Detects repeated sequences of actions beyond threshold.                         |
| `getMostActiveObject()`                         | None                         | `string`                                               | Returns the object with the most actions applied during the session.            |

---

##### 6. Scoring & Verdicts

| Method                   | Inputs / Parameters | Return Type          | Description / Purpose                                                                      |
| ------------------------ | ------------------- | -------------------- | ------------------------------------------------------------------------------------------ |
| `getAuthenticityScore()` | None                | `number` (0–100)     | Computes an explainable score for workflow authenticity.                                   |
| `getFlags()`             | None                | `Array<string>`      | Returns a list of integrity warnings or behavioral flags.                                  |
| `getEduHealth()`         | None                | `{ status: "healthy" | "warning"                                                                                  | "critical"; reasons: string[] }` | Returns overall session health assessment. |
| `getAssessmentVerdict()` | None                | `string`             | Human-readable verdict summarizing session authenticity, progress, and integrity concerns. |

---

##### 7. Charts & Visualization (Plotly Data)

| Method                            | Inputs / Parameters | Return Type     | Description / Purpose                        |
| --------------------------------- | ------------------- | --------------- | -------------------------------------------- |
| `getPlotlySceneGrowthOverTime()`  | None                | `Plotly.Data[]` | Vertices / objects over time.                |
| `getPlotlyActionDensity()`        | None                | `Plotly.Data[]` | Actions-per-minute density chart.            |
| `getPlotlyActionTypePie()`        | None                | `Plotly.Data[]` | Action-type distribution pie chart.          |
| `getPlotlyEntropyTrend()`         | None                | `Plotly.Data[]` | Action entropy over time.                    |
| `getPlotlyIdleTimeTraces()`       | None                | `Plotly.Data[]` | Idle periods timeline.                       |
| `getPlotlyAuthenticityScorePie()` | None                | `Plotly.Data[]` | Pie chart showing score breakdown vs issues. |

---

##### 8. Export & Serialization

| Method                                            | Inputs / Parameters  | Return Type | Description / Purpose                                                                               |
| ------------------------------------------------- | -------------------- | ----------- | --------------------------------------------------------------------------------------------------- |
| `getSummary()`                                    | None                 | `object`    | Aggregated KPIs, flags, metrics, and scores for dashboards or export.                               |
| `toJSON()`                                        | None                 | `object`    | Serializable JSON representing current Analyzer state; can be reloaded later via `parseFromJSON()`. |
| `exportCSV(options?: { includeFlags?: boolean })` | Optional CSV options | `string`    | Returns CSV string suitable for audits, research, or LMS integration.                               |

---

#### Types

| **Name**                 | **Category** | **Description**                      | **Notes / Details**                                                                                                                                                                     |
| ------------------------ | ------------ | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ISODateString`          | Type         | String representing an ISO 8601 date | `string` type alias                                                                                                                                                                     |
| `MajikBlenderEduJSON`    | Interface    | Full log dataset for a student       | Contains `id`, `data` (`RawActionLogEntry[]`), `total_working_time`, `period`, `timestamp`, optional `secret_key` and `student_id`, plus `stats`                                        |
| `RawActionLogJSON`       | Interface    | Raw log data structure               | Contains `data`, `status`, `total_working_time`, `period`, `stats` (`v`, `f`, `o`)                                                                                                      |
| `LogPeriod`              | Interface    | Start/end of a logging period        | `start` and `end` as `ISODateString`                                                                                                                                                    |
| `RawActionLogEntry`      | Interface    | Individual raw log entry             | `t` (timestamp number), `a` (action), `o` (object), `ot` (object type), `d` (details), `dt` (duration), `s` (stats: `v/f/o`), `ph` (previous hash)                                      |
| `ActionLogEntry`         | Interface    | Processed log entry                  | `timestamp`, `actionType`, `name`, `type`, optional `details`, `duration`, `sceneStats`, `hash`                                                                                         |
| `SceneStats`             | Interface    | Scene statistics                     | `vertex`, `face`, `object` counts                                                                                                                                                       |
| `RawSceneStats`          | Interface    | Raw scene statistics                 | `v`, `f`, `o` counts                                                                                                                                                                    |
| `HealthSeverity`         | Type         | Severity of log health               | `"healthy"                                                                                                                                                                              | "warning" | "critical"` |
| `ActionLogHealth`        | Interface    | Health status of a log               | `status` (`HealthSeverity`) and array of `reasons`                                                                                                                                      |
| `MajikBlenderEduSummary` | Interface    | Summary stats for a student/session  | Includes totals (`totalLogs`, `totalWorkingTime`, `effectiveTime`), idle stats, total vertices/objects, `mostActiveObject`, `actionCounts`, `score`, `flags`, `verdict`, `entropyScore` |
| `DefaultColors`          | Interface    | Predefined colors                    | `green`, `red`, `blue`, `white`                                                                                                                                                         |

---

#### Utils / Functions

| **Name**                                               | **Category** | **Description**                                      | **Notes**                                                             |
| ------------------------------------------------------ | ------------ | ---------------------------------------------------- | --------------------------------------------------------------------- |
| `fernetKeyFromString(password, salt)`                  | Crypto       | Generates Fernet-compatible key from password + salt | Uses PBKDF2 + SHA256, returns base64url                               |
| `sha256Hex(data)`                                      | Crypto       | SHA256 hash of string, hex-encoded                   | Used internally for integrity & key derivation                        |
| `aesEncrypt(metadata, key, salt)`                      | Crypto       | Encrypt JSON metadata using Fernet/AES               | Low-level; returns encoded string                                     |
| `aesDecrypt(encryptedMetadata, key, salt)`             | Crypto       | Decrypt Fernet/AES metadata                          | Low-level; returns string                                             |
| `encryptMetadata(metadata, key, salt)`                 | Crypto       | High-level encryption wrapper                        | Validates salt and hashes key before encryption                       |
| `decryptMetadata(encryptedMetadata, key, salt)`        | Crypto       | High-level decryption wrapper                        | Returns parsed JSON object                                            |
| `deepSortKeys(obj)`                                    | Helper       | Recursively sorts object keys                        | Used for canonical JSON before hashing                                |
| `computeEntryHash(entry)`                              | Hashing      | Computes SHA256 hash for a `RawActionLogEntry`       | Excludes `ph` and normalizes `"dt":0 → 0.0`                           |
| `generateGenesisKey(teacherKey, studentId)`            | Crypto       | Generates unique genesis key                         | Combines teacher key + studentId, SHA256 hash                         |
| `validateGenesisKey(current, teacherKey, studentId)`   | Crypto       | Validates genesis key                                | Returns boolean                                                       |
| `validateLogIntegrity(rawLogs, teacherKey, studentId)` | Crypto       | Validates sequential log hashes                      | Checks genesis + chain of entry hashes                                |
| `calculateDuration(previousEntry?, currentEntry?)`     | Time         | Computes elapsed seconds between logs                | Safely returns 0 if invalid                                           |
| `isSessionStartLog(entry)`                             | Helper       | Checks if entry is session start                     | `actionType="Session Started"`, `name="__SESSION__"`, `type="SYSTEM"` |


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
The Analyzer web tool and the [`@thezelijah/majik-blender-edu-analyzer`](https://www.npmjs.com/package/@thezelijah/majik-blender-edu-analyzer) NPM package are licensed under the **Apache License 2.0**.
* This is a permissive license that allows for broader integration into various software environments, including commercial and proprietary projects.
* This ensures developers can build custom dashboards or automated grading systems using our logic without GPL restrictions.
* See the [LICENSE-APACHE](LICENSE-APACHE) file for full details (or visit the [Apache 2.0 Official Site](https://www.apache.org/licenses/LICENSE-2.0)).
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
