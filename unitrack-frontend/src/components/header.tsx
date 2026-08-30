import React, { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";
const Header: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [active, setActive] = useState("home");

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "home", label: "Home" },
    { name: "features", label: "Features" },
    { name: "testimonials", label: "Testimonials" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-500 ${
        isScrolled ? "bg-white/90 backdrop-blur-md shadow-md" : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between py-4 px-6">
        {/* Logo */}
        <a
          href="#"
          className="flex items-center gap-2"
        >
          <div className="w-9 h-9 rounded-full bg-green-600 flex items-center justify-center text-white font-bold">
            <GraduationCap />
          </div>
          <span
            className={`text-xl font-semibold transition-colors duration-300 ${
              isScrolled ? "text-green-700" : "text-gray-900"
            }`}
          >
            Unitrack
          </span>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <button
              key={link.name}
              onClick={() => setActive(link.name)}
              className={`relative font-medium text-sm uppercase transition-colors duration-300 ${
                isScrolled
                  ? "text-green-800 hover:text-green-600"
                  : "text-gray-900 hover:text-green-200"
              }`}
            >
              {link.label}
              {active === link.name && (
                <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-green-600 rounded-full"></span>
              )}
            </button>
          ))}

          <button className="ml-4 cursor-pointer bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-full font-medium shadow-md transition-transform hover:scale-105">
            <Link to="/auth/login">Login</Link>
          </button>
        </nav>

        {/* Mobile Toggle */}
        <button
          className={`md:hidden p-2 rounded-lg ${
            isScrolled ? "text-green-800" : "text-gray-900"
          }`}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>

      {/* Mobile Nav */}
      {menuOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-md border-t border-green-200 shadow-lg">
          <nav className="flex flex-col items-center py-4 space-y-4">
            {navLinks.map((link) => (
              <button
                key={link.name}
                onClick={() => {
                  setActive(link.name);
                  setMenuOpen(false);
                }}
                className={`text-base font-medium uppercase ${
                  active === link.name
                    ? "text-green-700 underline"
                    : "text-green-800 hover:text-green-600"
                }`}
              >
                {link.label}
              </button>
            ))}
            <button className="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-full font-medium shadow-md">
              <Link to="/auth/login">Login</Link>
            </button>
          </nav>
        </div>
      )}

      {/* Mirror */}
      {isScrolled && (
        <div className="absolute bottom-0 left-0 w-full h-[2px] bg-linear-to-r from-green-600/60 via-white/40 to-green-600/60 transform scale-y-[-1] opacity-60"></div>
      )}
    </header>
  );
};

export default Header;
