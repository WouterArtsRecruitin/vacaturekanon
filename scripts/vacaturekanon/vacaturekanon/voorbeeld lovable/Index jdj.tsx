import Header from "@/components/landing/Header";
import Hero from "@/components/landing/Hero";
import AboutCompany from "@/components/landing/AboutCompany";
import VideoSection from "@/components/landing/VideoSection";
import JobDescription from "@/components/landing/JobDescription";
import Benefits from "@/components/landing/Benefits";
import ApplySection from "@/components/landing/ApplySection";
import Footer from "@/components/landing/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Hero />
      <AboutCompany />
      <VideoSection />
      <JobDescription />
      <Benefits />
      <ApplySection />
      <Footer />
    </div>
  );
};

export default Index;
