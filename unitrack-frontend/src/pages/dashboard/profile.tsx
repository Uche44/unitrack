import React, { useState } from "react";
import { useUserStore } from "../../context/user-context";
import { useProfile } from "../../hooks/use-profile";
import toast from "react-hot-toast";

const ProfilePage: React.FC = () => {
  const user = useUserStore((state) => state.user);
  const {
    areasOfExpertise,
    setAreasOfExpertise,
    projectInterests,
    setProjectInterests,
    savingField,
    error: profileError,
    save,
  } = useProfile();

  const role = user?.role ?? null;
  const showExpertise = role === "supervisor";
  const showInterests = role === "student";

  const [expertiseDraft, setExpertiseDraft] = useState<string | null>(null);
  const [interestsDraft, setInterestsDraft] = useState<string | null>(null);

  const expertiseValue = expertiseDraft ?? areasOfExpertise;
  const interestsValue = interestsDraft ?? projectInterests;

  if (!user) {
    return (
      <section className="p-8 text-center text-gray-500">Loading profile...</section>
    );
  }

  return (
    <section className="py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl md:text-3xl font-bold text-green-700 mb-2">
        Profile
      </h1>
      <p className="text-sm text-gray-600 mb-6">
        Keep your information up to date so the admin's supervisor recommendation
        tool can match you accurately.
      </p>

      {showExpertise && (
        <div className="bg-white shadow-md border border-dashed border-green-600 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-green-700 mb-2">
            Areas of expertise
          </h2>
          <p className="text-sm text-gray-600 mb-3">
            Topics you can supervise. Separate with commas or new lines.
          </p>
          <textarea
            value={expertiseValue}
            onChange={(event) => {
              setExpertiseDraft(event.target.value);
              setAreasOfExpertise(event.target.value);
            }}
            placeholder="e.g. nlp, computer vision"
            maxLength={500}
            rows={3}
            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-gray-500">
              {expertiseValue.length}/500
            </span>
            <button
              onClick={async () => {
                try {
                  await save("areas_of_expertise", expertiseValue);
                  toast.success("Areas of expertise saved.");
                } catch (caught) {
                  toast.error(
                    caught instanceof Error
                      ? caught.message
                      : "Failed to save profile",
                  );
                }
              }}
              disabled={savingField === "areas_of_expertise"}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50"
            >
              {savingField === "areas_of_expertise" ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      )}

      {showInterests && (
        <div className="bg-white shadow-md border border-dashed border-green-600 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-green-700 mb-2">
            Project interests
          </h2>
          <p className="text-sm text-gray-600 mb-3">
            Topics you'd like to work on. Admins use this to suggest a
            supervisor. Separate with commas or new lines.
          </p>
          <textarea
            value={interestsValue}
            onChange={(event) => {
              setInterestsDraft(event.target.value);
              setProjectInterests(event.target.value);
            }}
            placeholder="e.g. recommender systems, machine learning"
            maxLength={500}
            rows={3}
            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-gray-500">
              {interestsValue.length}/500
            </span>
            <button
              onClick={async () => {
                try {
                  await save("project_interests", interestsValue);
                  toast.success("Project interests saved.");
                } catch (caught) {
                  toast.error(
                    caught instanceof Error
                      ? caught.message
                      : "Failed to save profile",
                  );
                }
              }}
              disabled={savingField === "project_interests"}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50"
            >
              {savingField === "project_interests" ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      )}

      {profileError && (
        <p className="text-sm text-red-600 mt-3">{profileError}</p>
      )}
    </section>
  );
};

export default ProfilePage;