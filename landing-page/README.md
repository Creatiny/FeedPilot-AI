# FeedPilot AI Landing Page

🚀 Professional landing page for FeedPilot AI - Formula Calculator for Feed Manufacturers

**Live Demo:** [Deploy to Vercel](#deployment)

---

## 📦 Quick Start (10 minutes)

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager
- Vercel account (free)
- Formspree account (free)

### Step 1: Install Dependencies

```bash
npm install
```

### Step 2: Configure Formspree

1. Visit https://formspree.io and create a free account
2. Create a new form
3. Copy your Form ID (e.g., `mqkzvwld`)
4. Open `components/CTA.tsx` line 8
5. Replace: `useForm("mqkzvwld")` with your Form ID

### Step 3: Run Locally

```bash
npm run dev
```

Visit http://localhost:3000

### Step 4: Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Follow the prompts:
- Login with GitHub
- Project name: `feedpilot-landing`
- Deploy: **Yes**

**Done!** You'll get a URL like: `https://feedpilot-landing.vercel.app`

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Animation | Framer Motion |
| Forms | Formspree |
| Deployment | Vercel |

---

## 📁 Project Structure

```
feedpilot-landing-page/
├── app/
│   ├── layout.tsx      # Global layout + SEO
│   ├── page.tsx        # Main landing page
│   └── globals.css     # Global styles
├── components/
│   ├── Hero.tsx        # Hero section
│   ├── Features.tsx    # Features grid
│   ├── Demo.tsx        # Video demo
│   ├── Pricing.tsx     # Pricing cards
│   ├── CTA.tsx         # Call-to-action form
│   └── Footer.tsx      # Footer
├── public/             # Static assets
├── package.json
├── tailwind.config.js
├── next.config.js
└── README.md
```

---

## 🎨 Customization

### Change Colors

Edit `tailwind.config.js`:

```js
colors: {
  primary: {
    500: '#22c55e', // Your brand color
  }
}
```

### Update Content

All text is in the component files. Simply edit the strings.

### Add Your Video

In `components/Demo.tsx`, replace the placeholder with:

```tsx
<video className="w-full h-full object-cover" controls>
  <source src="/your-video.mp4" type="video/mp4" />
</video>
```

Place your video file in `public/` folder.

---

## 📊 Features

✅ **Responsive Design** - Mobile, tablet, desktop  
✅ **SEO Optimized** - Meta tags, Open Graph, Twitter cards  
✅ **Fast Performance** - Next.js static generation  
✅ **Analytics Ready** - Vercel Analytics compatible  
✅ **Conversion Focused** - Multiple CTAs, trust signals  
✅ **Easy Deployment** - One-click Vercel deploy  

---

## 🎯 Sections Included

1. **Hero** - Value proposition + CTAs
2. **Features** - 6 key features grid
3. **Demo** - Video showcase
4. **Pricing** - 3-tier pricing cards
5. **CTA** - Email capture form
6. **Footer** - Links + social media

---

## 📝 License

MIT License - Feel free to use for your projects!

---

## 🆘 Support

Need help? 

- Documentation: https://nextjs.org/docs
- Vercel Guide: https://vercel.com/docs
- Formspree Docs: https://help.formspree.io

---

**Built with ❤️ for FeedPilot AI**
