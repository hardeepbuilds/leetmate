# LeetMate

A competitive LeetCode progress tracker built for my college students. See how students stack up against thier classmates in real time.

## Features

- Sign up and log in with just a username and password — no email needed
- Connect your LeetCode account to automatically sync your stats
- See your total, easy, medium, and hard problems solved
- Compare your progress against friends with a gap indicator
- College-wide leaderboard ranked by problems solved, filterable by branch
- See how many classmates are online right now
- Stats auto-refresh every 30 minutes in the background

## Tech Stack

**Backend:** FastAPI, SQLite, bcrypt, JWT (python-jose), httpx, APScheduler

**Frontend:** Vanilla HTML, CSS, JavaScript

**Deployment:** Railway (backend), Vercel (frontend)

# LeetMate — Frontend

Static frontend for LeetMate, a competitive LeetCode tracker for college students.

Built with vanilla HTML, CSS, and JavaScript. Deployed on Vercel.

**Backend repo:** [leetmate-backend](https://github.com/hardeepbuilds/leetmate-backend)

## Pages

- `sign_ip_page.html` — signup and login
- `dashboard.html` — your stats, friends comparison, online count
- `leaderboard.html` — college-wide rankings with branch filter