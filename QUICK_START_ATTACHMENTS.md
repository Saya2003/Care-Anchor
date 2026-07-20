# Quick Start: File Attachments

## Install (One-Time Setup)

```bash
pip install pypdf2 python-docx
```

Then restart backend:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

## Use

1. Click 📎 button in chat
2. Select image or document
3. Send message
4. AI reads and responds!

## Supported Files

✅ Images: JPG, PNG, GIF, WebP  
✅ PDF documents  
✅ Word documents (.docx)  
✅ Text files (.txt)

Max size: 10MB

## What AI Can Read

- Prescriptions → Medication names, dosages
- Lab reports → Results, abnormal values
- Medical records → Patient history, diagnoses
- Vital signs → Blood pressure, heart rate, etc.
- Photos → Wounds, equipment, monitors
- Any text document → Full content extraction

## Done! 🎉

The AI agent is now ready to read your attached files!
