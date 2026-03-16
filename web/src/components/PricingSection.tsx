import { motion } from "framer-motion";
import { Check } from "lucide-react";

const tiers = [
  {
    name: "Starter",
    desc: "1 Tenant, Basic WhatsApp commerce, Order & Payment tracking.",
    price: "20,000 rwf",
    period: "/mo after trial",
    features: ["1 Tenant", "Payment link generation", "Instant confirmations", "Basic sales reports", "Email support"],
    highlighted: false,
  },
  {
    name: "Pro",
    desc: "Up to 10 Tenants, Multi-brand dashboards, Reports.",
    price: "50,000 rwf",
    period: "/mo after trial",
    features: ["Up to 10 Tenants", "Multi-brand dashboards", "Advanced sales reports", "Priority support"],
    highlighted: true,
  },
  {
    name: "Enterprise",
    desc: "Unlimited Tenants, Custom workflows, Priority support.",
    price: "Custom",
    period: " pricing",
    features: ["Unlimited Tenants", "Custom workflows", "Dedicated account manager", "SLA guarantee"],
    highlighted: false,
  },
];

const PricingSection = () => (
  <section id="pricing" className="bg-secondary py-16 md:py-24">
    <div className="container">
      <h2 className="text-center text-3xl font-bold md:text-4xl">Pricing</h2>

      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {tiers.map((t, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            // className={`relative rounded-xl border bg-card p-6 ${
            //   t.highlighted ? "border-accent shadow-lg ring-2 ring-accent" : "border-border"
            // }`}
          >
            {/* {t.highlighted && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-accent px-3 py-0.5 text-xs font-semibold text-accent-foreground">
                Most Popular
              </span>
            )} */}
            <h3 className="text-lg font-bold">{t.name}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{t.desc}</p>
            <p className="mt-4">
              <span className="text-3xl font-extrabold">{t.price}</span>
              <span className="text-sm text-muted-foreground">{t.period}</span>
            </p>
            <p className="mt-1 text-xs font-medium text-primary">Free for 14 days</p>
            <ul className="mt-6 space-y-3">
              {t.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-primary" />
                  {f}
                </li>
              ))}
            </ul>
            {/* <a
              href="#contact"
              className={`mt-6 block rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition-opacity hover:opacity-90 ${
                t.highlighted
                  ? "bg-accent text-accent-foreground"
                  : "bg-primary text-primary-foreground"
              }`}
            >
              Start Your 14-Day Free Trial
            </a> */}
          </motion.div>
        ))}
      </div>
    </div>
  </section>
);

export default PricingSection;
