/**
 * SettingsPanel LLM 真实 API 开关与连接测试 UI 测试
 *
 * 验证「使用真实 API」开关、Provider 切换自动填充、连接测试状态、
 * 以及保存配置时发送 config.llm AetherMessage。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SettingsPanel } from '../src/components/settings/SettingsPanel'
import { useSettingsStore } from '../src/store/settingsStore'
import * as laapStore from '../src/store/laapStore'
import { testConnection } from '../src/laap/llm'

vi.mock('../src/laap/llm', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../src/laap/llm')>()
  return {
    ...actual,
    testConnection: vi.fn(),
  }
})

const sendAetherMessageMock = vi.fn()

function resetStores() {
  window.localStorage.clear()
  useSettingsStore.setState({
    ...useSettingsStore.getState(),
    useRealApi: false,
    llm: {
      provider: 'deepseek',
      model: 'deepseek-v4-pro',
      creds: {},
      baseUrl: 'https://api.deepseek.com',
    },
  })
  useSettingsStore.getState().resetToDefaults()
}

describe('SettingsPanel LLM 真实 API', () => {
  beforeEach(() => {
    resetStores()
    vi.spyOn(laapStore, 'getCognitiveBus').mockReturnValue({
      sendAetherMessage: sendAetherMessageMock,
    } as unknown as ReturnType<typeof laapStore.getCognitiveBus>)
    vi.mocked(testConnection).mockReset()
    sendAetherMessageMock.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('「使用真实 API」开关存在并可点击', async () => {
    render(<SettingsPanel open onClose={() => {}} />)
    fireEvent.click(screen.getByText('LLM'))

    const checkbox = screen.getByRole('checkbox', {
      name: /开启后请求将转发到真实 LLM provider/i,
    }) as HTMLInputElement
    expect(checkbox).toBeDefined()
    expect(checkbox.checked).toBe(false)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(false)
  })

  it('Provider 切换时 endpoint 与 model 自动填充', async () => {
    render(<SettingsPanel open onClose={() => {}} />)
    fireEvent.click(screen.getByText('LLM'))

    const [providerSelect, modelSelect] = screen.getAllByRole('combobox') as HTMLSelectElement[]
    expect(providerSelect.value).toBe('deepseek')
    expect(modelSelect.value).toBe('deepseek-v4-pro')
    expect((screen.getByPlaceholderText('https://api.deepseek.com') as HTMLInputElement).value).toBe('https://api.deepseek.com')

    fireEvent.change(providerSelect, { target: { value: 'openai' } })

    await waitFor(() => {
      expect(providerSelect.value).toBe('openai')
      expect(modelSelect.value).toBe('gpt-5.5')
      expect((screen.getByPlaceholderText('https://api.openai.com/v1') as HTMLInputElement).value).toBe('https://api.openai.com/v1')
    })
  })

  it('点击「连接测试」按钮后显示成功状态', async () => {
    vi.mocked(testConnection).mockResolvedValueOnce({ ok: true, models: ['m1', 'm2'] })

    render(<SettingsPanel open onClose={() => {}} />)
    fireEvent.click(screen.getByText('LLM'))

    const keyInput = screen.getByPlaceholderText(/输入 DeepSeek API Key/i) as HTMLInputElement
    fireEvent.change(keyInput, { target: { value: 'sk-test' } })

    fireEvent.click(screen.getByRole('button', { name: /连接测试/i }))

    await waitFor(() => {
      expect(screen.getByText('连接成功')).toBeDefined()
    })

    expect(testConnection).toHaveBeenCalledOnce()
    const config = vi.mocked(testConnection).mock.calls[0][0]
    expect(config.provider).toBe('deepseek')
    expect(config.apiKey).toBe('sk-test')
  })

  it('点击「连接测试」按钮后显示失败状态', async () => {
    vi.mocked(testConnection).mockResolvedValueOnce({ ok: false, error: '密钥无效' })

    render(<SettingsPanel open onClose={() => {}} />)
    fireEvent.click(screen.getByText('LLM'))

    const keyInput = screen.getByPlaceholderText(/输入 DeepSeek API Key/i) as HTMLInputElement
    fireEvent.change(keyInput, { target: { value: 'sk-bad' } })

    fireEvent.click(screen.getByRole('button', { name: /连接测试/i }))

    await waitFor(() => {
      expect(screen.getByText('密钥无效')).toBeDefined()
    })
  })

  it('保存配置时发送 config.llm AetherMessage', async () => {
    render(<SettingsPanel open onClose={() => {}} />)
    fireEvent.click(screen.getByText('LLM'))

    const checkbox = screen.getByRole('checkbox', {
      name: /开启后请求将转发到真实 LLM provider/i,
    }) as HTMLInputElement
    fireEvent.click(checkbox)

    const keyInput = screen.getByPlaceholderText(/输入 DeepSeek API Key/i) as HTMLInputElement
    fireEvent.change(keyInput, { target: { value: 'sk-save' } })

    fireEvent.click(screen.getByRole('button', { name: /保存/i }))

    await waitFor(() => {
      expect(sendAetherMessageMock).toHaveBeenCalledOnce()
    })

    const message = sendAetherMessageMock.mock.calls[0][0]
    expect(message.topic).toBe('config.llm')
    expect(message.type).toBe('config_update')
    expect(message.payload).toMatchObject({
      provider: 'deepseek',
      apiKey: 'sk-save',
      model: 'deepseek-v4-pro',
      baseUrl: 'https://api.deepseek.com',
      useRealApi: true,
    })
  })
})
