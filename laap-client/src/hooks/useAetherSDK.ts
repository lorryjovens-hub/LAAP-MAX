/**
 * useAetherSDK — 在 React 组件中访问 AetherSDK 的 Hook
 *
 * 用法:
 *   const { sdk, memory, tool } = useAetherSDK()
 *   const tools = await tool.list()
 */

import { createContext, useContext } from 'react'
import { AetherSDK } from '../laap/sdk'
import { getCognitiveBus } from '../store/laapStore'
import type { CognitiveBusClient } from '../laap/bus'

let _sdkInstance: AetherSDK | null = null

export function getAetherSDK(): AetherSDK {
  if (!_sdkInstance) {
    _sdkInstance = new AetherSDK(getCognitiveBus(), { debug: true })
  }
  return _sdkInstance
}

export function resetAetherSDK(): void {
  _sdkInstance = null
}

export const AetherSDKContext = createContext<AetherSDK | null>(null)

export interface AetherSDKAccess {
  sdk: AetherSDK
  bus: CognitiveBusClient
}

export function useAetherSDK(): AetherSDKAccess {
  const sdk = useContext(AetherSDKContext) ?? getAetherSDK()
  return { sdk, bus: sdk.bus }
}

export default useAetherSDK
