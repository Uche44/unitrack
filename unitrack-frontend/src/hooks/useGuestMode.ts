import { useUserStore } from "../context/user-context";

export const useGuestMode = () => {
  const is_guest = useUserStore((state) => state.is_guest);
  const guest_role = useUserStore((state) => state.guest_role);

  return {
    isGuest: is_guest,
    guestRole: guest_role,
    isReadOnly: is_guest,
  };
};
