import { Mail, MapPin } from "lucide-react";

const ContactSection = () => (
  <section id="contact" className="bg-secondary py-16 md:py-24">
    <div className="container mx-auto max-w-xl text-center">
      <h2 className="text-3xl font-bold md:text-4xl">Get in Touch</h2>
      <p className="mt-3 text-muted-foreground">Have questions? We'd love to hear from you.</p>
      <div className="mt-8 space-y-4">
        <a href="mailto:support@tonihub.net" className="flex items-center justify-center gap-2 text-foreground hover:text-primary">
          <Mail className="h-5 w-5" />
          support@tonihub.net
        </a>
        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <MapPin className="h-5 w-5" />
          Kigali, Rwanda
        </div>
      </div>
    </div>
  </section>
);

export default ContactSection;
