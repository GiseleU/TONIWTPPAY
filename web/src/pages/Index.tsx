import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import HowItWorks from "@/components/HowItWorks";
import FeaturesSection from "@/components/FeaturesSection";
import WhoItsFor from "@/components/WhoItsFor";
import TechnologySection from "@/components/TechnologySection";
import PricingSection from "@/components/PricingSection";
import CompanySection from "@/components/CompanySection";
import ContactSection from "@/components/ContactSection";
import Footer from "@/components/Footer";

const Index = () => (
  <div className="min-h-screen">
    <Header />
    <HeroSection />
    <HowItWorks />
    <FeaturesSection />
    <WhoItsFor />
    <TechnologySection />
    <PricingSection />
    <CompanySection />
    <ContactSection />
    <Footer />
  </div>
);

export default Index;
