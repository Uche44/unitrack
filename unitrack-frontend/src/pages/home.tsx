import Hero from "../components/hero";
import Header from "../components/header";
import Features from "../components/features";
import Testimonials from "../components/testimonials";
import Footer from "../components/footer";
const Home: React.FC = () => {
  return (
    <section className="w-full min-h-screen">
      <Header />
      <Hero />
      <Features />
      <Testimonials />
      <Footer/>
    </section>
  );
};

export default Home;
