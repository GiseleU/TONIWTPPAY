import { motion } from "framer-motion";
import heroMockup from "@/assets/hero_phone_mockup.png";
import { Shield, Smartphone, Lock } from "lucide-react";

const trustSignals = [
  { icon: Smartphone, label: "Powered by Meta WhatsApp Business API" },
  { icon: Shield, label: "MoMo Certified" },
  { icon: Lock, label: "GDPR/CCPA Compliant" },
];

const HeroSection = () => (
  <section className="overflow-hidden py-16 md:py-24">
    <div className="container grid items-center gap-12 md:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-4xl font-extrabold leading-tight tracking-tight md:text-5xl lg:text-6xl">
          Sell and Manage Orders Directly from{" "}
          <span className="text-primary">WhatsApp</span>
        </h1>
        <p className="mt-4 max-w-lg text-lg text-muted-foreground">
          ToniWtpPay helps businesses capture customer inquiries, confirm orders, and track payments — all through WhatsApp conversations.
        </p>

        {/* Trust Signals */}
        {/* <div className="mt-8 flex flex-wrap gap-4">
          {trustSignals.map((s) => (
            <div key={s.label} className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-medium text-muted-foreground">
              <s.icon className="h-4 w-4 text-primary" />
              {s.label}
            </div>
          ))}
        </div> */}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="flex justify-center"
      >
        <img src={heroMockup} alt="WhatsApp commerce phone mockup showing order management and MoMo payment confirmation" className="w-full max-w-xs md:max-w-sm" loading="eager" />
      </motion.div>
    </div>
  </section>
);

export default HeroSection;
