"use client";

import { motion } from "framer-motion";
import { Check, Star } from "lucide-react";

const plans = [
  {
    name: "Free",
    price: 0,
    period: "forever",
    description: "Try before you buy",
    features: [
      "10 calculations per day",
      "Price lookup (69+ ingredients)",
      "Formula cost calculator",
      "Telegram bot access",
      "Community support",
    ],
    cta: "Start Free",
    popular: false,
  },
  {
    name: "Starter",
    price: 9.99,
    period: "month",
    description: "For individual dealers",
    features: [
      "50 calculations per day",
      "All Free features",
      "Customer records",
      "Price alerts & reminders",
      "7-day free trial",
      "Email support",
    ],
    cta: "Start 7-Day Trial",
    popular: true,
  },
  {
    name: "Pro",
    price: 29.99,
    period: "month",
    description: "For power users",
    features: [
      "Unlimited calculations",
      "All Starter features",
      "Nutrition analysis",
      "Custom ingredients",
      "PDF/Excel export",
      "Priority support",
      "Referral rewards",
    ],
    cta: "Start 7-Day Trial",
    popular: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="section-padding bg-white">
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
            Simple, Transparent <span className="gradient-text">Pricing</span>
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Start with a 7-day free trial. No credit card required.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative card ${
                plan.popular ? "border-2 border-green-500 shadow-2xl scale-105" : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                    <Star className="w-4 h-4" />
                    Most Popular
                  </div>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-slate-900 mb-2">
                  {plan.name}
                </h3>
                <p className="text-slate-600 text-sm mb-4">
                  {plan.description}
                </p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-5xl font-bold text-slate-900">
                    ${plan.price}
                  </span>
                  <span className="text-slate-600">/{plan.period}</span>
                </div>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href="https://t.me/feedpilot_bot"
                target="_blank"
                rel="noopener noreferrer"
                className={`block w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 text-center ${
                  plan.popular
                    ? "btn-primary"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-900"
                }`}
              >
                {plan.cta}
              </a>
            </motion.div>
          ))}
        </div>

        {/* Trust message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-center mt-12"
        >
          <p className="text-slate-600">
            <span className="font-semibold">7-day free trial</span> on Starter and Pro plans. 
            Cancel anytime. No questions asked.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
