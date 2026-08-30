import React from "react";
import { motion } from "framer-motion";

interface Testimonial {
  quote: string;
  name: string;
  role: string;
  avatar?: string;
}

const testimonials: Testimonial[] = [
  {
    quote:
      "UniTrack transformed my final year project experience. Tracking submissions and getting feedback was incredibly smooth!",
    name: "Sarah Chen",
    role: "Computer Science Student",
    avatar: "https://i.pravatar.cc/100?img=1",
  },
  {
    quote:
      "As a supervisor, UniTrack has made managing multiple student projects so much easier. The integrated feedback feature is a game-changer.",
    name: "Dr. David Lee",
    role: "Engineering Department Supervisor",
    avatar: "https://i.pravatar.cc/100?img=2",
  },
  {
    quote:
      "The intuitive interface and clear overview of project progress helped me stay organized and on track. Highly recommend UniTrack!",
    name: "Amir Khan",
    role: "Business IT Student",
    avatar: "https://i.pravatar.cc/100?img=3",
  },
];

const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};

const Testimonials: React.FC = () => {
  return (
    <section
      className="py-20 bg-white"
      id="testimonials"
    >
      <div className="max-w-6xl mx-auto px-6 text-center">
        {/* Header */}
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-3xl md:text-4xl font-bold text-green-800 mb-12"
        >
          What Our Users Say
        </motion.h2>

       
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t, i) => (
            <motion.div
              key={i}
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              transition={{ duration: 0.6, delay: i * 0.2 }}
              viewport={{ once: true }}
              className="bg-white border border-green-100 rounded-2xl shadow-md hover:shadow-lg p-8 transition-all duration-300"
            >
              <p className="text-green-800 italic mb-6 leading-relaxed">
                “{t.quote}”
              </p>

              <div className="flex items-center justify-center gap-3">
                {t.avatar && (
                  <img
                    src={t.avatar}
                    alt={t.name}
                    className="w-10 h-10 rounded-full object-cover border border-green-200"
                  />
                )}
                <div className="text-left">
                  <p className="font-semibold text-green-900">{t.name}</p>
                  <p className="text-green-600 text-sm">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
