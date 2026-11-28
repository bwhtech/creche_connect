import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
	presets: [frappeUIPreset],
	content: [...frappeUIContent.filter((glob) => !/\/(experimental|vitepress)\//.test(glob)), './index.html', './src/**/*.{vue,js,ts}'],
}
