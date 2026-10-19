import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
	presets: [frappeUIPreset],
	content: [...frappeUIContent, './index.html', './src/**/*.{vue,js,ts}'],
}
