import { motion } from "framer-motion";
import { MessageCircle, Package, CreditCard, LineChart, Sparkles } from "lucide-react";

const features = [
  { icon: MessageCircle, title: "WhatsApp Commerce", desc: "Capture and manage customer inquiries directly from WhatsApp." },
  { icon: Package, title: "Order Management", desc: "Convert inquiries into confirmed orders." },
  { icon: CreditCard, title: "Payment Tracking", desc: "Track customer payments and order completion." },
  { icon: LineChart, title: "Business Insights", desc: "Daily summaries and activity reports." },
];

const FeaturesSection = () => (
  <section id="Features" className="py-16 md:py-24">
    <div className="container">
      <h2 className="text-center text-3xl font-bold md:text-4xl">Core Features</h2>
      <p className="mx-auto mt-3 max-w-xl text-center text-muted-foreground">
        Everything you need to run your business from WhatsApp.
      </p>

      <div className="mt-12 grid gap-6 sm:grid-cols-2">
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            className="rounded-xl border border-border bg-card p-6 transition-shadow hover:shadow-lg"
          >
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <f.icon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
          </motion.div>
        ))}
      </div>

      {/* Ecosystem Teaser */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="mt-8 p-6 text-center"
      >
        {/* <div className="mb-3 flex justify-center">
          <Sparkles className="h-6 w-6 text-accent-foreground" />
        </div>
        <h3 className="text-lg font-semibold">Coming Soon — CRM, Inventory, Advanced AI Tools</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          We're expanding the ToniHub ecosystem. Be the first to know.
        </p> */}
        <a
          href="#contact"
          className="mt-4 inline-block text-3xl rounded-lg bg-accent px-6 py-2.5 font-semibold text-accent-foreground transition-opacity hover:opacity-90"
        >
          Join Waitlist
        </a>
      </motion.div>
    </div>
  </section>
);

export default FeaturesSection;
