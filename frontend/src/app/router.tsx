import { createBrowserRouter } from "react-router";

import ForgotPasswordController from "../features/auth/controllers/ForgotPasswordController/ForgotPasswordController";
import ResetPasswordController from "../features/auth/controllers/ResetPasswordController/ResetPasswordController";
import SignInController from "../features/auth/controllers/SignInController/SignInController";
import SignUpController from "../features/auth/controllers/SignUpController/SignUpController";
import VerifyEmailController from "../features/auth/controllers/VerifyEmailController/VerifyEmailController";
import CommandCenterController from "../features/capture/controllers/CommandCenterController/CommandCenterController";
import MemoryDetailController from "../features/records/controllers/MemoryDetailController/MemoryDetailController";
import RecordDetailController from "../features/records/controllers/RecordDetailController/RecordDetailController";
import ReminderDetailController from "../features/records/controllers/ReminderDetailController/ReminderDetailController";
import RecordsController from "../features/records/controllers/RecordsController/RecordsController";
import SettingsController from "../features/settings/controllers/SettingsController/SettingsController";
import AppShell from "./AppShell";
import RequireAuth from "./RequireAuth";

export const router = createBrowserRouter([
  { path: "/sign-up", element: <SignUpController /> },
  { path: "/verify-email", element: <VerifyEmailController /> },
  { path: "/sign-in", element: <SignInController /> },
  { path: "/forgot-password", element: <ForgotPasswordController /> },
  { path: "/reset-password", element: <ResetPasswordController /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <CommandCenterController /> },
          { path: "/records", element: <RecordsController /> },
          { path: "/records/:id", element: <RecordDetailController /> },
          { path: "/records/reminders/:id", element: <ReminderDetailController mode="VIEW" /> },
          { path: "/records/reminders/:id/edit", element: <ReminderDetailController mode="EDIT" /> },
          { path: "/records/memories/:id", element: <MemoryDetailController mode="VIEW" /> },
          { path: "/records/memories/:id/edit", element: <MemoryDetailController mode="EDIT" /> },
          { path: "/settings", element: <SettingsController /> },
        ],
      },
    ],
  },
]);
