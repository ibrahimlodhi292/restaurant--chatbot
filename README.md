# Restaurant Chatbot

A single-page AI chatbot for a restaurant. Users can ask about the menu, prices, hours, location, and reservations. The AI answers **only** from the hardcoded restaurant data — no hallucination.

---

## Folder Structure

```
restaurant-chatbot/
├── backend/
│   ├── main.py               # FastAPI app (streaming /chat endpoint)
│   ├── restaurant_data.json  # All restaurant info the AI can use
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html            # Single-page chat UI
│   └── vercel.json           # Vercel static deployment config
└── .gitignore
```

---

## Local Development

### 1. Backend

```bash
cd backend

# Copy env file and fill in your key
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --port 8000
```

Backend is now running at `http://localhost:8000`

### 2. Frontend

Open `frontend/index.html` directly in a browser, **or** serve it with:

```bash
cd frontend
npx serve .          # or: python -m http.server 5500
```

Before opening, edit `index.html` line ~76 and set:

```js
const BACKEND_URL = "http://localhost:8000";
```

---

## Deployment

### Backend → Render

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Connect your repo, set **Root Directory** to `backend`.
4. Fill in the settings:
   | Field | Value |
   |---|---|
   | Environment | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
5. Add **Environment Variables**:
   | Key | Value |
   |---|---|
   | `OPENAI_API_KEY` | your OpenAI key |
   | `OPENAI_MODEL` | `gpt-4o-mini` (or `gpt-4o`) |
   | `ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
6. Click **Deploy**. Copy the URL (e.g. `https://restaurant-chatbot-api.onrender.com`).

### Frontend → Vercel

1. Edit `frontend/index.html`, find this line near the bottom:
   ```js
   const BACKEND_URL = "https://your-backend.onrender.com";
   ```
   Replace with your actual Render URL.

2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your repo.
3. Set **Root Directory** to `frontend`.
4. Click **Deploy**. Done.

---

## Customise the Restaurant

Edit `backend/restaurant_data.json` — change the name, location, menu, prices, hours, etc.  
The AI will automatically use the updated data. No code changes needed.

---

## Example Request / Response

**POST** `http://localhost:8000/chat`

```json
{
  "message": "What pizzas do you have and how much are they?",
  "session_id": null
}
```

**Streaming SSE response:**

```
data: {"type": "start", "session_id": "abc-123"}

data: {"type": "chunk", "content": "We have the "}
data: {"type": "chunk", "content": "Margherita Pizza for $14.00. "}
data: {"type": "chunk", "content": "Would you like to know about other items?"}

data: {"type": "end"}
```

**Unknown question:**

```
User: Do you have lobster?
Bot:  I don't have that information.
```

---

## AI Rules (enforced via system prompt)

- Answers ONLY from `restaurant_data.json`
- NEVER invents items, prices, or policies
- Unknown info → `"I don't have that information."`
- Stays in character as a restaurant receptionist
- Concise, polite responses
