"use client";

import { motion } from "framer-motion";

export default function Demo() {
  return (
    <section id="demo" className="section-padding bg-gradient-to-b from-slate-50 to-white">
      <div className="container-custom">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            See It in <span className="gradient-text">Action</span>
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Watch how FeedPilot AI calculates a complete broiler formula in under 10 seconds
          </p>
        </motion.div>

        {/* Video Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-5xl mx-auto"
        >
          <div className="relative aspect-video bg-slate-900 rounded-2xl shadow-2xl overflow-hidden">
            <video
              className="w-full h-full object-cover"
              controls
              autoPlay={false}
              preload="metadata"
            >
              <source src="/feedpilot-demo.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
