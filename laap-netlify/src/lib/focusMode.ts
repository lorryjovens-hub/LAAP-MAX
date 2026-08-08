import { getLocalConfig, setLocalConfig } from '@/lib/db';

const FOCUS_MODE_KEY = 'focus_mode';

export async function getFocusMode(userId?: string): Promise<boolean> {
  try {
    return (await getLocalConfig<boolean>(FOCUS_MODE_KEY, userId)) ?? false;
  } catch {
    return false;
  }
}

export async function saveFocusMode(value: boolean, userId?: string): Promise<void> {
  try {
    await setLocalConfig(FOCUS_MODE_KEY, value, userId);
  } catch {
    // ignore persistence errors
  }
}
