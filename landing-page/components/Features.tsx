"use client";

import { motion } from "framer-motion";
import { Clock, Database, DollarSign, TrendingUp, Shield, Zap } from "lucide-react";

const features = [
  {
    icon: Clock,
    title: "10-Second Calculation",
    description: "Generate complete feed formulas in seconds, not hours. 360x faster than manual methods.",
    color: "text-blue-600",
    bgColor: "bg-blue-100",
  },
  {
    icon: Database,
    title: "NRC Standards",
    description: "Built-in nutritional requirements for poultry, swine, cattle, and aquaculture species.",
    color: "text-green-600",
    bgColor: "bg-green-100",
  },
  {
    icon: DollarSign,
    title: "USDA Real-Time Prices",
    description: "Live ingredient pricing from USDA/AMS sources. Optimize costs automatically.",
    color: "text-yellow-600",
    bgColor: "bg-yellow-100",
  },
  {
    icon: TrendingUp,
    title: "Cost Optimization",
    description: "AI suggests alternative ingredients to reduce costs while maintaining nutritional balance.",
    color: "text-purple-600",
    bgColor: "bg-purple-100",
  },
  {
    icon: Shield,
    title: "Quality Assurance",
    description: "Automatic compliance checks and nutritional deficiency warnings before production.",
    color: "text-red-600",
    bgColor: "bg-red-100",
  },
  {
    icon: Zap,
    title: "Multi-Species Support",
    description: "Broilers, layers, sows, pigs, beef cattle, dairy cows, fish, and shrimp.",
    color: "text-indigo-600",
    bgColor: "bg-indigo-100",
  },
];

export default function Features() {
  return (
    <section id="features" className="section-padding bg-white">
      <div className="container-custom">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Everything You Need to{" "}
            <span className="gradient-text">Formulate Faster</span>
          </h2>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            Professional-grade tools designed for feed manufacturers and nutritionists
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="card"
            >
              <div className={`${feature.bgColor} ${feature.color} w-14 h-14 rounded-xl flex items-center justify-center mb-6`}>
                <feature.icon className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
