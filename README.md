# DocuSensei - AI Document Assistant

A modern AI-powered document assistant with Flask backend, featuring a sleek black netted background, document upload capability, and an interactive chat interface.

## Features

- 🎨 **Dashing Black Netted Background**: Animated grid pattern background
- 💬 **Interactive Chat Interface**: Real-time chat with AI assistant
- 📄 **Document Upload**: Support for TXT, PDF, DOC, DOCX, JSON, CSV files
- 💾 **Chat History**: Saves previous conversations locally
- ⚙️ **Response Settings**: Adjustable response detail (Detailed/Balanced/Concise)
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
bput-bot/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Main HTML template
├── static/
│   ├── style.css      # Styles with netted background
│   └── script.js      # Frontend JavaScript
└── uploads/           # Uploaded files directory
```

## Usage

1. **Start a New Chat**: Click the "New Chat" button
2. **Upload Documents**: Click "Attach file" at the bottom to upload documents
3. **Ask Questions**: Type your message or click a suggestion card
4. **Adjust Settings**: Choose response detail level (Detailed/Balanced/Concise)
5. **View History**: Access previous chats from the sidebar

## Customization

- Modify `app.py` to integrate with actual AI models
- Adjust colors and animations in `static/style.css`
- Extend functionality in `static/script.js`

## Notes

- Maximum file size: 16MB
- Supported file types: TXT, PDF, DOC, DOCX, JSON, CSV
- Chat history is saved locally in browser
- The current implementation uses an echo bot - integrate with your preferred AI API

Enjoy DocuSensei! 🎓✨
