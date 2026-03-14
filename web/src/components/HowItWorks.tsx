import { motion } from "framer-motion";
import { MessageSquare, ClipboardList, CheckCircle, BarChart3 } from "lucide-react";

const steps = [
  { icon: MessageSquare, title: "Customer Sends a Message", desc: "A customer sends a WhatsApp message to your business." },
  { icon: ClipboardList, title: "Inquiry & Order Recorded", desc: "ToniWtpPay records the inquiry and order automatically." },
  { icon: CheckCircle, title: "Seller Confirms the Order", desc: "You confirm the order using simple commands." },
  { icon: BarChart3, title: "Payment & Status Tracked", desc: "Payment and order status are tracked in real-time." },
];

const HowItWorks = () => (
  <section id="how-it-works" className="bg-secondary py-16 md:py-24">
    <div className="container">
      <h2 className="text-center text-3xl font-bold md:text-4xl">How It Works</h2>
      <p className="mx-auto mt-3 max-w-xl text-center text-muted-foreground">
        Four simple steps to turn WhatsApp conversations into managed orders.
      </p>

      <div className="relative mx-auto mt-12 max-w-2xl">
        <div className="absolute left-6 top-0 hidden h-full w-px bg-border md:block" />

        <div className="space-y-10">
          {steps.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="flex gap-4 md:gap-6"
            >
              <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <s.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step {i + 1}</p>
                <h3 className="mt-1 text-lg font-semibold">{s.title}</h3>
                <p className="mt-1 text-muted-foreground">{s.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default HowItWorks;
