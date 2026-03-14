import { motion } from "framer-motion";
import { Server, Shield, Zap } from "lucide-react";

const TechnologySection = () => (
  <section className="py-16 md:py-24">
    <div className="container">
      <h2 className="text-center text-3xl font-bold md:text-4xl">Built for Reliability</h2>
      <p className="mx-auto mt-3 max-w-2xl text-center text-muted-foreground">
        ToniWtpPay is built on the WhatsApp Business Platform and modern cloud infrastructure, integrating seamlessly with WhatsApp to help businesses manage customer conversations and transactions securely.
      </p>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="mx-auto mt-10 grid max-w-3xl gap-6 sm:grid-cols-3"
      >
        {[
          { icon: Server, title: "Cloud Infrastructure", desc: "Scalable and always available." },
          { icon: Shield, title: "End-to-End Security", desc: "Your data is encrypted and protected." },
          { icon: Zap, title: "Real-time Sync", desc: "Instant updates across all channels." },
        ].map((t, i) => (
          <div key={i} className="text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <t.icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold">{t.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{t.desc}</p>
          </div>
        ))}
      </motion.div>
    </div>
  </section>
);

export default TechnologySection;
