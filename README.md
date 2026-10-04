# Girl Safety Assistant — Vercel + Gemini

Same frontend design as the original project, with the chat powered by Gemini through a Vercel Python serverless function.

## Deploy to Vercel

1. Upload this folder to a GitHub repository.
2. Import the repository into Vercel.
3. In **Vercel → Project → Settings → Environment Variables**, add:
   - `GEMINI_API_KEY` = your Gemini API key
   - `GEMINI_MODEL` = `gemini-2.5-flash` (optional)
4. Redeploy.

The frontend calls `/api/chat`; the API key is never placed in browser JavaScript.

## Local test

Vercel's local runtime is recommended for testing. Install the Vercel CLI and run:

`vercel dev`

Then open the local URL shown by Vercel.
