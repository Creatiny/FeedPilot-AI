"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { useForm } from "@formspree/react";
import { CheckCircle, Loader2 } from "lucide-react";

export default function CTA() {
  // TODO: Replace with your Formspree form ID
  const [state, handleSubmit] = useForm("mqkzvwld"); // Get your ID at https://formspree.io
  const [email, setEmail] = useState("");

  if (state.succeeded) {
    return (
      <section className="section-padding bg-gradient-to-br from-green-500 to-blue-600">
        <div className="container-custom">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center text-white max-w-2xl mx-auto"
          >
            <CheckCircle className="w-16 h-16 mx-auto mb-6" />
            <h2 className="text-4xl font-bold mb-4">You're on the list!</h2>
            <p className="text-xl text-white/90">
              We'll contact you within 24 hours to set up your free trial.
            </p>
          </motion.div>
        </div>
      </section>
    );
  }

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
            Join 50+ feed manufacturers using FeedPilot AI. 
            Start your 1-month free trial today.
          </p>

          {/* Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit({ email });
            }}
            className="flex flex-col sm:flex-row gap-4 max-w-xl mx-auto"
          >
            <input
              type="email"
              name="email"
              placeholder="Enter your work email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1 px-6 py-4 rounded-xl text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-4 focus:ring-white/30 text-lg"
            />
            <button
              type="submit"
              disabled={state.submitting}
              className="btn-primary bg-white text-green-600 hover:bg-slate-50 disabled:opacity-70 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {state.submitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Sending...
                </span>
              ) : (
                "Start Free Trial"
              )}
            </button>
          </form>

          <p className="text-sm text-white/80 mt-6">
            No credit card required • 1-month free trial • Cancel anytime
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
