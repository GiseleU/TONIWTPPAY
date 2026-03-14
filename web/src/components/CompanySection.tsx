import { motion } from "framer-motion";

const CompanySection = () => (
  <section className="py-16 md:py-24">
    <div className="container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="mx-auto max-w-2xl text-center"
      >
        <h2 className="text-3xl font-bold md:text-4xl">About ToniHub</h2>
        <p className="mt-4 text-muted-foreground leading-relaxed">
          ToniWtpPay is developed and operated by <strong className="text-foreground">ToniHub</strong>, a technology company building tools to help African businesses grow using messaging platforms.
        </p>
      </motion.div>
    </div>
  </section>
);

export default CompanySection;
