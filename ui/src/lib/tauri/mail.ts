import {
  parseConversations,
  parseDeviceLogin,
  parseFetchResult,
  parseMailDetail,
  parseMailStatus,
  type DeviceLogin,
  type MailConversation,
  type MailDetail,
  type MailFetchResult,
  type MailStatus,
} from "../mail";
import { engineRequest } from "./engine";

export async function getMailStatus(): Promise<MailStatus> {
  return parseMailStatus(await engineRequest("mail.status"));
}

export async function startMailLogin(): Promise<DeviceLogin> {
  return parseDeviceLogin(await engineRequest("mail.connect-start"));
}

export async function finishMailLogin(login: DeviceLogin): Promise<void> {
  await engineRequest("mail.connect-finish", login);
}

export async function disconnectMail(): Promise<void> {
  await engineRequest("mail.disconnect");
}

export async function fetchMail(): Promise<MailFetchResult> {
  return parseFetchResult(await engineRequest("mail.fetch"));
}

export async function listConversations(): Promise<MailConversation[]> {
  return parseConversations(await engineRequest("mail.list"));
}

export async function readConversation(id: string): Promise<MailDetail> {
  return parseMailDetail(await engineRequest("mail.read", { id }));
}

export async function exportConversation(id: string, target: string): Promise<void> {
  await engineRequest("mail.export", { id, target });
}

export async function removeConversation(id: string): Promise<void> {
  await engineRequest("mail.remove", { id });
}
