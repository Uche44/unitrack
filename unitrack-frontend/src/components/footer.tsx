import React from "react";
import { motion } from "framer-motion";
import { Github, Linkedin, Mail } from "lucide-react";

const Footer: React.FC = () => {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      viewport={{ once: true }}
      className="w-full bg-green-50 border-t border-green-100 text-green-800 py-8 px-6 md:px-12"
    >
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 text-center md:text-left">
        {/* Left Section */}
        <div>
          <p className="font-semibold text-lg text-green-700">UniTrack</p>
          <p className="text-sm text-green-600 mt-1">
            Join UniTrack today and experience smarter project management.
          </p>
        </div>

        {/* Social Icons */}
        <div className="flex items-center gap-5">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-green-700 hover:text-green-900 transition-colors duration-200"
            aria-label="GitHub"
          >
            <Github size={22} />
          </a>
          <a
            href="https://linkedin.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-green-700 hover:text-green-900 transition-colors duration-200"
            aria-label="LinkedIn"
          >
            <Linkedin size={22} />
          </a>
          <a
            href="mailto:contact@unitrack.com"
            className="text-green-700 hover:text-green-900 transition-colors duration-200"
            aria-label="Email"
          >
            <Mail size={22} />
          </a>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-green-100 my-6"></div>

      {/* Bottom Text */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between text-xs md:text-sm text-green-600 gap-2">
        <p>
          © {new Date().getFullYear()}{" "}
          <span className="font-semibold text-green-800">UniTrack</span>. All
          rights reserved.
        </p>
        <div className="flex flex-col md:flex-row items-center gap-1 md:gap-4">
          {/* <p>
            Powered by{" "}
            <span className="font-medium text-green-800">Your University</span>
          </p> */}
          <p>
            Developed by{" "}
            <span className="font-medium text-green-800">Perpetual Asogwa</span>
          </p>
        </div>
      </div>
    </motion.footer>
  );
};

export default Footer;
