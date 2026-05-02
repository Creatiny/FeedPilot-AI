"use client";

import { motion } from "framer-motion";
import { CheckCircle, ArrowRight } from "lucide-react";

export default function CTA() {
  return (
    <section className="section-padding bg-gradient-to-br from-green-500 to-blue-600">
      <div className="container-custom">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center text-white max-w-3xl mx-auto"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Calculate 360x Faster?
          </h2>
          <p className="text-xl text-white/90 mb-10">
            Join early users trying FeedPilot AI.
            Start your 7-day free trial today.
          </p>

          {/* CTA Button */}
          <a
            href="https://t.me/feedpilot_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 bg-white text-green-600 hover:bg-slate-50 px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300"
          >
            Start Free Trial on Telegram
            <ArrowRight className="w-5 h-5" />
          </a>

          <p className="text-sm text-white/80 mt-6">
            No credit card required • 7-day free trial • Cancel anytime
          </p>

          {/* Trust badges */}
          <div className="flex flex-wrap justify-center items-center gap-6 mt-10">
            <div className="flex items-center gap-2 text-white/90">
              <CheckCircle className="w-5 h-5" />
              <span>NRC Certified</span>
            </div>
            <div className="flex items-center gap-2 text-white/90">
              <CheckCircle className="w-5 h-5" />
              <span>USDA Data</span>
            </div>
            <div className="flex items-center gap-2 text-white/90">
              <CheckCircle className="w-5 h-5" />
              <span>Secure & Private</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
