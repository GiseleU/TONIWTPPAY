import Header from "@/components/Header";
import Footer from "@/components/Footer";

const Privacy = () => (
  <div className="min-h-screen">
    <Header />
    <main className="py-16 md:py-24">
      <article className="container mx-auto max-w-prose">
        <h1 className="text-3xl font-bold md:text-4xl">Privacy Policy</h1>
        <p className="mt-2 text-sm text-muted-foreground">Last updated: March 2026</p>

        <div className="mt-10 space-y-8 text-muted-foreground leading-relaxed">
          <section id="data-collection">
            <h2 className="text-xl font-semibold text-foreground">1. Data We Collect</h2>
            <p className="mt-2">
              We collect information you provide when using ToniWtpPay, including your business name, contact details, and WhatsApp messages exchanged between you and your customers for order processing. We also collect usage data such as access times and feature usage to improve our service.
            </p>
          </section>

          <section id="data-processing">
            <h2 className="text-xl font-semibold text-foreground">2. How WhatsApp Messages Are Processed</h2>
            <p className="mt-2">
              TONIWTPPay operates on the official WhatsApp Business Platform. When you interact with our service, we process relevant transaction data — such as payment link requests and confirmation notifications — to facilitate payments and generate reports. We do not store the content of personal conversations.
            </p>
          </section>

          <section id="data-storage">
            <h2 className="text-xl font-semibold text-foreground">3. How Data Is Stored and Protected</h2>
            <p className="mt-2">
              All data is stored on encrypted servers hosted in secure cloud infrastructure. We use industry-standard encryption (TLS in transit, AES-256 at rest) and follow best practices to protect your business data and your customers' information. Access is restricted to authorized personnel only.
            </p>
          </section>

          <section id="data-sharing">
            <h2 className="text-xl font-semibold text-foreground">4. Data Sharing</h2>
            <p className="mt-2">
              We do not sell your data. We may share information with trusted service providers who assist in operating our platform, subject to strict confidentiality agreements. We may also disclose information when required by law.
            </p>
          </section>

          <section id="your-rights">
            <h2 className="text-xl font-semibold text-foreground">5. Your Rights</h2>
            <p className="mt-2">
              You may request access to, correction of, or deletion of your data at any time by contacting us. You may also request that we stop processing your data, subject to legal or contractual obligations.
            </p>
          </section>

          <section id="contact-privacy">
            <h2 className="text-xl font-semibold text-foreground">6. Contact Us</h2>
            <p className="mt-2">
              For any privacy-related questions, please contact us at{" "}
              <a href="mailto:support@tonihub.net" className="text-primary hover:underline">
                support@tonihub.net
              </a>.
            </p>
          </section>
        </div>
      </article>
    </main>
    <Footer />
  </div>
);

export default Privacy;
