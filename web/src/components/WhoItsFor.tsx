import { motion } from "framer-motion";

const audiences = ["Restaurants", "Retail Shops", "Market Vendors", "Delivery Businesses"];

const WhoItsFor = () => (
  <section className="bg-secondary py-16 md:py-24">
    <div className="container text-center">
      <h2 className="text-3xl font-bold md:text-4xl">Who It's For</h2>
      <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
        Small to medium businesses that receive orders through WhatsApp.
      </p>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="mt-8 flex flex-wrap justify-center gap-3"
      >
        {audiences.map((a) => (
          <span key={a} className="rounded-full border border-border bg-card px-5 py-2 text-sm font-medium">
            {a}
          </span>
        ))}
      </motion.div>
    </div>
  </section>
);

export default WhoItsFor;
