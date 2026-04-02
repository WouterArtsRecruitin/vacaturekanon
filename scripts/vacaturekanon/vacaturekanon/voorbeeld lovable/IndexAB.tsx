import heroBg from "@/assets/hero-bg.jpg";
import { Button } from "@/components/ui/button";
import { Wrench, MapPin, Euro, Users, Shield, Truck } from "lucide-react";

const benefits = [
  {
    icon: Euro,
    title: "Uitstekend Salaris",
    description: "Competitief salaris van €2.800 - €3.800 bruto per maand, afhankelijk van ervaring.",
  },
  {
    icon: Truck,
    title: "Eigen Servicebus",
    description: "Volledig uitgeruste servicebus met professioneel gereedschap en onderdelen.",
  },
  {
    icon: Users,
    title: "Hecht Team",
    description: "Werk samen met ervaren collega's in een informele en collegiale sfeer.",
  },
  {
    icon: Shield,
    title: "Pensioenregeling",
    description: "Goede pensioenopbouw en uitgebreide secundaire arbeidsvoorwaarden.",
  },
  {
    icon: Wrench,
    title: "Opleidingen",
    description: "Doorlopende technische trainingen en persoonlijke ontwikkelingsmogelijkheden.",
  },
  {
    icon: MapPin,
    title: "Regio Gebonden",
    description: "Werk in je eigen regio met minimale reistijd. Diverse standplaatsen beschikbaar.",
  },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-primary/95 backdrop-blur-md border-b border-primary">
        <div className="container mx-auto flex items-center justify-between h-16 px-4">
          <span className="font-heading text-xl font-bold text-primary-foreground tracking-tight">
            AEBI SCHMIDT
          </span>
          <Button variant="hero" size="sm" onClick={() => document.getElementById("solliciteer")?.scrollIntoView({ behavior: "smooth" })}>
            Direct Solliciteren
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <img
          src={heroBg}
          alt="Service monteur aan het werk bij Aebi Schmidt"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 hero-overlay" />
        <div className="relative container mx-auto px-4 py-32">
          <div className="max-w-2xl space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-accent/20 border border-accent/30 px-4 py-1.5 text-sm font-medium text-accent animate-fade-in">
              <Wrench className="w-4 h-4" />
              Vacature — Service Monteur
            </div>
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-bold text-primary-foreground leading-tight animate-fade-up">
              Word{" "}
              <span className="text-gradient">Service Monteur</span>
              <br />
              bij Aebi Schmidt
            </h1>
            <p className="text-lg text-primary-foreground/80 max-w-lg animate-fade-up" style={{ animationDelay: "0.15s" }}>
              Zet jouw technisch talent in voor 's werelds toonaangevende fabrikant van straat- en winterdienstvoertuigen. Zelfstandig werken, afwisselende klussen, en groei in je vak.
            </p>
            <div className="flex flex-wrap gap-4 animate-fade-up" style={{ animationDelay: "0.3s" }}>
              <Button variant="hero" size="xl" onClick={() => document.getElementById("solliciteer")?.scrollIntoView({ behavior: "smooth" })}>
                Bekijk de Vacature
              </Button>
              <Button variant="heroOutline" size="xl" onClick={() => document.getElementById("voordelen")?.scrollIntoView({ behavior: "smooth" })}>
                Waarom Aebi Schmidt?
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section id="voordelen" className="py-24 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-xl mx-auto mb-16">
            <p className="text-accent font-semibold font-heading text-sm uppercase tracking-widest mb-3">Waarom wij?</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground">
              Wat wij jou bieden
            </h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((b, i) => (
              <div
                key={b.title}
                className="group p-6 rounded-xl bg-card border border-border hover:border-accent/40 hover:shadow-lg hover:shadow-accent/5 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                  <b.icon className="w-6 h-6 text-accent" />
                </div>
                <h3 className="font-heading text-lg font-semibold text-foreground mb-2">{b.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{b.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Job Details */}
      <section className="py-24 bg-primary">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-16">
            <div>
              <p className="text-accent font-semibold font-heading text-sm uppercase tracking-widest mb-3">Functieomschrijving</p>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold text-primary-foreground mb-8">
                Wat ga je doen?
              </h2>
              <ul className="space-y-4">
                {[
                  "Zelfstandig uitvoeren van onderhoud en reparaties aan machines bij klanten op locatie",
                  "Diagnose stellen van storingen aan hydraulische, elektrische en mechanische systemen",
                  "Montage en inbedrijfstelling van nieuwe machines en opbouwen",
                  "Bijhouden van serviceverslagen en digitale werkorders",
                  "Adviseren van klanten over onderhoud en optimaal gebruik van hun machines",
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-primary-foreground/85">
                    <div className="mt-1.5 w-2 h-2 rounded-full bg-accent shrink-0" />
                    <span className="text-sm leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-accent font-semibold font-heading text-sm uppercase tracking-widest mb-3">Profiel</p>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold text-primary-foreground mb-8">
                Wat breng je mee?
              </h2>
              <ul className="space-y-4">
                {[
                  "MBO-diploma Werktuigbouwkunde, Mechatronica of vergelijkbare richting",
                  "Minimaal 2 jaar ervaring als monteur in de buitendienst",
                  "Kennis van hydrauliek, elektrotechniek en dieselmotoren",
                  "Rijbewijs B (BE is een pré)",
                  "Zelfstandig, klantgericht en oplossingsgericht",
                  "Goede beheersing van de Nederlandse taal",
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-primary-foreground/85">
                    <div className="mt-1.5 w-2 h-2 rounded-full bg-accent shrink-0" />
                    <span className="text-sm leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="solliciteer" className="py-24 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center space-y-6">
            <p className="text-accent font-semibold font-heading text-sm uppercase tracking-widest">Interesse?</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground">
              Solliciteer nu als Service Monteur
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Herken jij jezelf in dit profiel? Neem contact met ons op of stuur direct je CV en motivatie.
              Wij nemen binnen 2 werkdagen contact met je op.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Button variant="hero" size="xl" asChild>
                <a href="mailto:hr@aebi-schmidt.nl?subject=Sollicitatie%20Service%20Monteur">
                  Stuur je CV
                </a>
              </Button>
              <Button variant="outline" size="xl" asChild>
                <a href="tel:+31888003000">
                  Bel ons: 088 800 3000
                </a>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-primary py-8 border-t border-primary">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="font-heading text-sm font-semibold text-primary-foreground/60">
            © 2026 Aebi Schmidt Nederland
          </span>
          <div className="flex items-center gap-6 text-sm text-primary-foreground/50">
            <a href="#" className="hover:text-accent transition-colors">Privacy</a>
            <a href="#" className="hover:text-accent transition-colors">Voorwaarden</a>
            <a href="https://www.aebi-schmidt.com" target="_blank" rel="noopener noreferrer" className="hover:text-accent transition-colors">aebi-schmidt.com</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
