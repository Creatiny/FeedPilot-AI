"use client";

import { motion } from "framer-motion";
import { Play, CheckCircle, ArrowRight } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-32 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-50 via-blue-50 to-white opacity-50" />
      
      <div className="container-custom relative z-10">
        <div className="text-center max-w-5xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-semibold mb-8"
          >
            <CheckCircle className="w-4 h-4" />
            Trusted by 50+ Feed Manufacturers in North America
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold text-slate-900 mb-6 leading-tight"
          >
            Calculate Feed Formulas in{" "}
            <span className="gradient-text">10 Seconds</span>
            <br />
            Instead of 1 Hour
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl md:text-2xl text-slate-600 mb-10 max-w-3xl mx-auto"
          >
            AI-powered formula calculator for feed manufacturers. 
            NRC standards, real-time USDA prices, 360x faster than manual calculations.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
          >
            <a href="#pricing" className="btn-primary inline-flex items-center gap-2">
              Start Free Trial
              <ArrowRight className="w-5 h-5" />
            </a>
            <a href="#demo" className="btn-secondary inline-flex items-center gap-2">
              <Play className="w-5 h-5" />
              Watch Demo (2:30)
            </a>
          </motion.div>

          {/* Trust indicators */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex flex-wrap justify-center items-center gap-8 text-sm text-slate-500"
          >
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>1-month free trial</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>NRC & USDA certified</span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
