import { Linkedin, Twitter, Mail } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 py-16">
      <div className="container-custom">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-1">
            <h3 className="text-2xl font-bold text-white mb-4">FeedPilot AI</h3>
            <p className="text-slate-400 mb-6">
              Professional feed formula calculator for manufacturers in North America and Australia.
            </p>
            <div className="flex gap-4">
              <a href="https://www.linkedin.com/company/feedpilot-ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                <Linkedin className="w-6 h-6" />
              </a>
              <a href="https://x.com/feedpilot_ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                <Twitter className="w-6 h-6" />
              </a>
              <a href="mailto:hello@feedpilot.ai" className="hover:text-white transition-colors">
                <Mail className="w-6 h-6" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-3">
              <li>
                <a href="#features" className="hover:text-white transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="#pricing" className="hover:text-white transition-colors">
                  Pricing
                </a>
              </li>
              <li>
                <a href="#demo" className="hover:text-white transition-colors">
                  Demo
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  API
                </a>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-white font-semibold mb-4">Company</h4>
            <ul className="space-y-3">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Blog
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Careers
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-3">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Cookie Policy
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm">
            © {new Date().getFullYear()} FeedPilot AI. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm">
            <span>Made with ❤️ for feed manufacturers</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
