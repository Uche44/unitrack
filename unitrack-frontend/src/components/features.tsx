import React from "react";
import {
  ClipboardList,
  MessageSquare,
  CalendarCheck,
  Users,
  Bell,
  FolderKanban,
} from "lucide-react";

const features = [
  {
    icon: <ClipboardList className="w-8 h-8 " />,
    title: "Streamlined Submissions",
    description:
      "Monitor your project milestones, upload documents, and track submission history with ease.",
  },
  {
    icon: <MessageSquare className="w-8 h-8 " />,
    title: "Integrated Feedback",
    description:
      "Receive detailed, version-controlled feedback from your supervisor directly on your submissions.",
  },
  {
    icon: <CalendarCheck className="w-8 h-8 " />,
    title: "Efficient Session Management",
    description:
      "Organize your project timeline and sessions, ensuring you meet all deadlines and stay on track.",
  },
  {
    icon: <Users className="w-8 h-8 " />,
    title: "Collaborative Workspace",
    description:
      "Seamlessly communicate with your supervisor and team members for guidance and approvals.",
  },
  {
    icon: <Bell className="w-8 h-8 " />,
    title: "Real-time Notifications",
    description:
      "Stay updated with instant alerts on feedback, new submissions, and important announcements.",
  },
  {
    icon: <FolderKanban className="w-8 h-8" />,
    title: "Centralized Resources",
    description:
      "Access shared project resources, templates, and guidelines from one convenient location.",
  },
];

const Features: React.FC = () => {
  return (
    <section
      className="py-20 bg-green-50"
      id="features"
    >
      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-green-800">
            Key Features Designed for Your Success
          </h2>
          <p className="text-green-700 mt-3 max-w-2xl mx-auto">
            Unitrack brings together all the tools you need to manage your
            academic projects efficiently.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group bg-white rounded-2xl shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-300 border border-green-100 p-8"
            >
              <div className="flex items-center justify-center w-14 h-14 bg-green-100 rounded-xl mb-6 group-hover:bg-green-600  transition-all duration-300">
                <div className="group-hover:text-white">{feature.icon}</div>
              </div>
              <h3 className="text-lg font-semibold text-green-800 mb-2">
                {feature.title}
              </h3>
              <p className="text-green-700 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
