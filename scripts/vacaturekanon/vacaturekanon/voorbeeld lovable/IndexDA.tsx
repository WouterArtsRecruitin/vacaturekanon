import { useState } from "react";
import Navbar from "@/components/Navbar";
import VersionSwitcher from "@/components/VersionSwitcher";
import HeroSection from "@/components/HeroSection";
import HeroSectionB from "@/components/HeroSectionB";
import HeroSectionC from "@/components/HeroSectionC";
import WhySection from "@/components/WhySection";
import WhySectionB from "@/components/WhySectionB";
import WhySectionC from "@/components/WhySectionC";
import VacanciesSection from "@/components/VacanciesSection";
import CultureSection from "@/components/CultureSection";
import CultureSectionB from "@/components/CultureSectionB";
import CultureSectionC from "@/components/CultureSectionC";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

type Version = "A" | "B" | "C";

const Index = () => {
  const [version, setVersion] = useState<Version>("A");

  const heroMap = { A: <HeroSection />, B: <HeroSectionB />, C: <HeroSectionC /> };
  const whyMap = { A: <WhySection />, B: <WhySectionB />, C: <WhySectionC /> };
  const cultureMap = { A: <CultureSection />, B: <CultureSectionB />, C: <CultureSectionC /> };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <VersionSwitcher current={version} onChange={setVersion} />
      <main>
        {heroMap[version]}
        {whyMap[version]}
        <VacanciesSection />
        {cultureMap[version]}
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
