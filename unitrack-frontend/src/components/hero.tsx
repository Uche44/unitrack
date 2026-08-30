import { Link } from "react-router-dom";

const Hero: React.FC = () => {
  return (
    <section className="w-full min-h-screen flex flex-col md:flex-row justify-center items-center gap-8 px-6 md:px-12 pt-24 md:pt-0">
      <div className="w-full md:w-[48%] text-center md:text-left">
        <h1 className="text-3xl md:text-5xl font-semibold">
          Manage your Final Year Projects Seamlessly
        </h1>
        <p className="text-base md:text-xl mt-4 md:pr-15">
          Streamline submissions, track feedback and collaborate with
          supervisors and peers. Making your final year project a success.
        </p>

        <div className="flex flex-wrap justify-center md:justify-start gap-3 mt-6">
          <Link
            to="/auth/students"
            className="bg-green-700 px-4 py-2 rounded-[5px] text-white cursor-pointer text-sm md:text-base"
          >
            Sign up as Student
          </Link>
          <Link
            to="/auth/supervisors"
            className="border-green-700 border-2 bg-white px-4 py-2 rounded-[5px] text-green-900 cursor-pointer text-sm md:text-base"
          >
            Sign up as Supervisor
          </Link>
        </div>
      </div>

      <img
        src="https://res.cloudinary.com/dcw1m1rak/image/upload/v1762958834/download_z5bfuq.jpg"
        alt="Students collaborating"
        className="w-full max-w-sm md:max-w-none md:w-[40%] md:h-[70vh] rounded-md object-cover"
      />
    </section>
  );
};

export default Hero;
