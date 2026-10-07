# User guide

Drawflow automates three tasks of the façade draftsman: the **parts list** (DWG/DXF drawings → Excel), the **report** (PDF drawings → Word) and the **submission** (XLSX or PDF → normalised table). Everything runs on your computer: no file ever leaves the machine.

Settings and their default values are described directly in the application (Settings); this guide explains how to use them.

## Getting started

The complete procedure, in order. Each step links to its section.

1. **Install Drawflow** and enter the access code (`0000` to begin with): [Install Drawflow](#install-drawflow).
2. **Open Settings → Setup** and configure every line marked "To configure": [Install the prerequisites](#install-the-prerequisites).
   1. **ODA File Converter** (for DWG files): **Install**, then accept the Windows permission prompt. If it fails, [download ODA](https://www.opendesign.com/guestfiles/oda_file_converter), install it, then **Scan again** and **Use**.
   2. **Model server**: **Install** Ollama, then **Start** if it does not respond.
   3. **Model**: **Choose a model** opens Settings → AI models; download the **Recommended** model, then **Use**.
3. **Adapt the features to your standard** (blocks, fields, columns, file names) in Settings: [Adapt a feature to your standard](#adapt-a-feature-to-your-standard).
4. **Optional — Stream Dock**: [Control with a Stream Dock](#control-with-a-stream-dock).
5. **Run a first run** from a feature's tab: [Run a feature](#run-a-feature). Save it as a preset to run it again in one click.
6. **Ask the assistant a question** (speech-bubble icon): [Use the assistant](#use-the-assistant).

If something goes wrong: [Troubleshooting](#troubleshooting).

### Language

Settings → **General** → **Language**: `fr` or `en`. The interface switches as soon as you save; on first launch it follows the Windows language.

## The Today screen

Drawflow opens on **Today**: missing prerequisites (**Configure** button), presets that can be run in one click, and the latest runs with **Open result** and **Run again**. Command `today.open` for the Stream Dock; the assistant reads the same screen ("what's waiting for me?").

## Install Drawflow

1. Download `Drawflow_X.Y.Z_x64-setup.exe` from the [latest release](https://github.com/pepito2t/drawflow-engine/releases/latest) and run it (installation for the current user, no administrator rights needed).
2. If Windows shows "unknown publisher" (SmartScreen): **More info → Run anyway**. The installer is not signed yet.
3. Enter the access code (see [Access code](#access-code)).
4. If a prerequisite is missing, the **Configure Drawflow** message opens the Setup screen.

## Install the prerequisites

**Settings → Setup** scans the computer and offers, for each prerequisite, the button that fixes it: install, start, download, or open the official page.

| Prerequisite | What it is for | Manual download |
|---|---|---|
| ODA File Converter | Reading DWG files (DXF files do not need it) | [Windows installer](https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi) · [Official page](https://www.opendesign.com/guestfiles/oda_file_converter) |
| Local model server (Ollama or LM Studio) and a model | Running the assistant | [Ollama](https://ollama.com/download) |
| Stream Dock software *(optional)* | Controlling Drawflow, and AutoCAD, from a Stream Dock (Mirabox) | [Mirabox](https://mirabox.net/pages/download) · [AutoCAD plugin](https://github.com/pepito2t/streamdock_autocad) |

- On Windows, **Install** downloads the official installer (latest version) with a progress bar, then installs it; Ollama is about 1.5 GB. On macOS, Ollama is installed through Homebrew. Otherwise, use the links above.
- You can leave the screen during an installation or a download: the progress is still there when you come back.
- Drawflow asks for confirmation before installing third-party software (you accept its licence) and before downloading a model (several GB).
- **Scan again** after a manual installation.

## Run a feature

1. Open the feature's tab; its instructions are under "How it works".
2. Add the files or folders (**Browse** or drag and drop).
3. Fill in the project name and the output folder. Drawflow **never** writes into the original files.
4. Click **Run**. For the parts list and the submission, the **preview before export** (checked by default) shows the table first: rows to check are highlighted (empty cell, unreadable amount), with an **Anomalies only** filter. **Export** writes the Excel file; **Cancel** writes nothing. Uncheck the preview in a preset meant for the Stream Dock to export directly.

At the end, the **warnings to check** block lists, file by file, what could not be processed as expected: where (sheet, title block, block) and what to do. **Copy** puts the report on the clipboard so you can send it. Warnings remain available in the History.

You can switch tabs or run another feature while a run is running. The **Runs** icon (next to the gear) shows the ones in progress; **Cancel** stops a run. A message signals the end, and a Windows notification if the run was long or if Drawflow was in the background.

### History

The **History** tab lists the latest runs (200 at most): date, duration, result or error, number of warnings. **Open result** opens the last file produced; **Run again** reloads the same files and runs again; **×** removes a row. Commands `history.open` and `history.rerun` for the Stream Dock and the assistant.

### Several projects in one list

Check **One project per folder** in the parts list: each folder of drawings becomes a project (its name), the list gets a **Project** column, and a **Total** sheet adds up identical parts across all projects — handy for a supplier order covering several sites.

### Compare two drawing revisions

The **Revision comparison** tab takes the drawings of the previous revision (A) and those of the new revision (B), builds both parts lists using the parts list standard, then compares them: parts **added**, **removed**, **quantities changed**, unchanged, and a **Drawings** sheet (present in A, in B, in both). Parts are matched by the columns chosen in Settings → Revision comparison (by default "Reference"). Numbered drawings (`01_facade-nord`, `facade-nord_02`) are recognised as the same drawing thanks to the increment pattern, adjustable in the same place.

### Adapt a feature to your standard

Each feature has its own category in Settings:

- **Parts list**: which blocks to keep (wildcards `*` and `?`), which AutoCAD attribute fills each column, how to count and group parts.
- **Report**: where the title block is on the page, which fields to read from it (label searched for, or regular expression with the `re:` prefix), format of the references.
- **Submission**: which headers to recognise for each column, which columns to convert to numbers.
- **Exported file names**: a template with variables (`{projet}`, `{date}`…), listed under the field.

**Export / Import** in each category shares a standard between computers.

### Excel and Word templates

**Settings → Templates**: import your templates and choose the default one for each feature. A template chosen in the form takes priority. The tags that can be used in a Word template are listed in the instructions of the Report tab.

### Full profile

Settings → **Profile** exports as one zip all the standards, the imported Excel and Word templates and the presets, without the access code or the local API token. On another computer, **Import a profile** shows what will be replaced before applying. A profile coming from a newer version of Drawflow is refused: update the application first.

### Presets

**Save as preset** (at the top of the tab) stores the form under a name, so you can reload it or run it from the Stream Dock.

### Watched folders

Settings → **Automations**: choose a folder and a preset. As soon as a drawing, a PDF or an Excel file is dropped there, the preset runs with that file, once per file and once the copy is complete. The application must be open and unlocked; a network folder is checked every few seconds.

## Use the assistant

The **speech-bubble** icon opens the chat panel. The assistant answers questions about Drawflow by consulting the application.

It can also **suggest a run** ("run the submission on C:\Chantier\Soumissions"): a card shows the feature and the inputs, and nothing starts until you click **Run**. The run then follows the normal path: progress in Runs, cancellation, notification.

- Prerequisite: a local model (see [Install the prerequisites](#install-the-prerequisites)). The server address must point to this computer: no data leaves the machine.
- **Settings → AI models** recommends the model suited to the computer's memory, and lets you search, download, use or delete a model (or download another one from the Ollama library by name).
- **Drag a file into the panel** (drawing, PDF, submission, Word): it appears as an attachment to the message; the assistant reads it on the computer, says what it contains and suggests the right feature. Nothing is copied or sent.
- **Why is this part missing?** The assistant reads the run in question (files produced, warnings with file and location) and answers by quoting the cause and the advice.
- **Submission not recognised**: ask the assistant to match the file's headers to the columns; it reads the file, suggests the matches in a card, and **Apply** saves them in Settings → Submission. Nothing is changed without that click.
- The list at the top of the panel switches model. **Stop** interrupts an answer, **+** starts a new conversation. The current conversation is kept on the computer between two launches (without the run cards).

## Mail (Exchange / Microsoft 365)

The **Mail** tab keeps your conversations on this computer, read-only: Drawflow does not move, flag or delete anything in the mailbox.

1. Settings → **Mail**: paste the Entra ID application ID (provided by the person who administers Drawflow); the tenant stays `common` for a work account.
2. Mail tab → **Connect the mailbox**: open the page shown, enter the code displayed, sign in with the mailbox account. The session stays valid from one launch to the next.
3. **Fetch new messages** (or the `mail.fetch` key on the Stream Dock): messages from the last few days (adjustable) are sorted by conversation, attachments included (except images and files over 25 MB).
4. Open a conversation to read it; **Export to a folder…** copies the readable messages and the attachments into a site folder; **Remove from Drawflow** deletes the local copy, never the original email.

Conversations are stored in `%APPDATA%\ch.drawflow.desktop\mail\` (folder can be changed); beyond the configured number, the oldest ones are removed.

## Control with a Stream Dock

Drawflow works with the Mirabox **Stream Dock** (Stream Dock software for Windows).

1. **Settings → Setup → Drawflow plugin for Stream Dock → Install the plugin**: Drawflow enables its local API and installs the plugin in Stream Dock.
2. **Restart Stream Dock** (it only loads a new plugin at startup).
3. In Stream Dock, drag an action from the **Drawflow** category onto a key; for a **Preset** or **Tab** key, choose the preset or the tab from the list.

The plugin connects on its own to the Drawflow installed on this computer: there is no port or token to enter. The key's fields are only needed if Drawflow runs under another Windows account (port and token in Settings → Local API).

Keys run a preset (progress, then green or red), open a tab, cancel runs, open the last result or count runs. They show "Locked" while Drawflow is locked, "Offline" when Drawflow is closed or the port does not answer, and "Invalid token" when Drawflow is open but the token or port entered in the key is wrong: copy the token from Settings → Local API. After a refused press (deleted preset, run already going…), the key shows the reason for three seconds.

**AutoCAD plugin**: the **AutoCAD plugin for Stream Dock** line installs in the same way the [streamdock_autocad](https://github.com/pepito2t/streamdock_autocad) plugin: macros, layers, toggles (ORTHO, snaps…) and AutoCAD status on the keys. It requires full AutoCAD (not LT), open while in use.

**Updates**: the Setup screen shows **Update** when a newer version of a plugin exists (after a Drawflow update, or a new version of the AutoCAD plugin). Click **Update**, then restart Stream Dock.

## Access code

Initial code: `0000`, to be changed in **Settings → Access code**. After several wrong attempts, an increasing delay is enforced.

**Forgotten code**: close Drawflow and delete `access-code.json` in `%APPDATA%\ch.drawflow.desktop\`; the code goes back to `0000`.

## Updates

At startup, Drawflow offers new versions (**Update** or **Later**). The update downloads while you keep working; it only installs when no run is in progress, stops any engine process still open (assistant, mail), then restarts the application. If the download fails, clicking again retries the update.

## What Drawflow has saved you

Settings → **About** counts the completed runs and the files processed on this computer, per feature, and derives the time saved (minutes per file adjustable in General, counters can be disabled). Nothing is sent anywhere.

## Where the files are

| Content | Location (Windows) |
|---|---|
| Settings, presets, run history, imported templates, access code, integrations | `%APPDATA%\ch.drawflow.desktop\` |
| Usage counters (`stats.json`) | `%APPDATA%\ch.drawflow.desktop\` |
| Diagnostic logs (`engine.log`) | `%APPDATA%\ch.drawflow.desktop\logs\` |
| Cache of converted DWG drawings | `%LOCALAPPDATA%\drawflow\cache\` (can be changed in Settings → General) |

## Troubleshooting

| Problem | Solution |
|---|---|
| "ODA File Converter is not configured" | Settings → Setup → **Install** or **Use** |
| The ODA installation fails | [Download the ODA installer](https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi), run it, then **Scan again** and **Use** |
| "The local model does not respond" | Settings → Setup → **Start**, or launch LM Studio |
| "The model … cannot be found" | Settings → Setup → **Download**, or choose an installed model in the panel |
| "The settings file is unreadable" | It is never overwritten: restore a backup or delete `settings.json` |
| Another error, or an error that keeps coming back | Settings → Setup → **Logs**: send `engine.log` (every failure is recorded there with the exact cause, for example Ollama's reply) |
| Stream Dock keys "Offline" | Launch Drawflow and check that the local API is enabled (Settings → Local API) |
| Stream Dock keys "Invalid token" | Drawflow is open but refuses the key: copy the token from Settings → Local API into the key settings, or clear the fields if Drawflow runs under the same Windows account |
