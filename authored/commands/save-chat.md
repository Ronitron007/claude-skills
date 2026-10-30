You are saving the current conversation to a markdown file for future reference.

## Arguments

$ARGUMENTS

Parse the arguments for:

- `scope`: Either `all` (entire conversation) or a number like `5` (last N
  messages). Default: `all`
- `folder`: Optional subfolder name within ~/Projects. Default: inferred from
  conversation context

Examples:

- `/save-chat` → saves entire chat, infers folder
- `/save-chat 5` → saves last 5 messages, infers folder
- `/save-chat all notes` → saves entire chat to ~/Projects/notes
- `/save-chat 10 estate-pulse` → saves last 10 messages to
  ~/Projects/estate-pulse

## Execution Steps

### 1. Parse Arguments

```
If arg is a number only → scope=<number>, folder=inferred
If arg is "all" only → scope=all, folder=inferred
If arg is "<number|all> <folder>" → use both
If no args → scope=all, folder=inferred
```

### 2. Infer Folder (if not provided)

Analyze the conversation to determine the most appropriate project folder:

- Look for project names, file paths, or repository references mentioned
- Check if working in a specific project context
- If unclear, use `chat-logs` as default folder

### 3. Create Directory

```bash
mkdir -p ~/Projects/<folder>/chats
```

### 4. Generate Filename

Use format: `chat-<YYYYMMDD>-<HHMM>-<brief-topic>.md`

Example: `chat-20260119-1430-browser-automation.md`

The brief topic (2-4 words, kebab-case) should summarize the main subject of the
conversation.

### 5. Format Chat Content

Create markdown with this structure:

```markdown
# Chat Log: <Topic Summary>

**Date**: <YYYY-MM-DD HH:MM> **Scope**: <Entire conversation | Last N messages>
**Project**: <folder name>

---

## Summary

<2-3 sentence summary of what was discussed/accomplished>

## Key Outcomes

- <Outcome 1>
- <Outcome 2>
- <Outcome 3>

---

## Conversation

### User

<message content>

### Assistant

<message content>

### User

<message content>

...
```

### 6. Write File

Save to: `~/Projects/<folder>/chats/chat-<timestamp>-<topic>.md`

### 7. Confirm

Report back:

```
✓ Saved to ~/Projects/<folder>/chats/<filename>
  • Scope: <all | last N messages>
  • Messages: <count>
  • Topic: <brief description>
```

## Formatting Rules

- Preserve code blocks with proper language tags
- Keep inline code formatting
- Maintain list structures
- For long code outputs, summarize with `<code output truncated>` if over 50
  lines
- Strip any system messages or metadata not relevant to the user
- If message contains file contents, include a reference like
  `[Contents of file.py]` rather than full dump if very long

## Edge Cases

- If conversation is very short (< 3 messages), still save but note it
- If scope number exceeds actual messages, save all available
- If folder has special characters, sanitize to alphanumeric + hyphens
