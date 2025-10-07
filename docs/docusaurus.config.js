// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer").themes.github;
const darkCodeTheme = require("prism-react-renderer").themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Midil Kit',
  tagline: 'A comprehensive Python SDK for backend systems development',
  url: 'https://docs.midil.io',
  baseUrl: '/midil-kit/',
  onBrokenLinks: 'throw',
  favicon: 'img/favicon.png',
  organizationName: 'midil-io',
  projectName: 'midil-kit',
  staticDirectories: ['static'],

  future: {
    experimental_faster: true, // Faster builds with Rspack
    v4: true, // Enable all Docusaurus v4 future flags
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: ({ locale, docPath }) => {
            return `https://github.com/midil-labs/midil-kit/edit/main/docs/docs/${docPath}`;
          },
          showLastUpdateTime: true,
          // Enable Mermaid diagrams
          remarkPlugins: [],
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
        sitemap: {
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/tags/**'],
          filename: 'sitemap.xml',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Midil Kit Documentation',
        logo: {
          alt: 'Midil Kit Logo',
          src: 'img/logo.svg',
          srcDark: 'img/logo-dark.svg', // Optional: add dark mode logo
        },
        items: [
          {
            to: '/',
            label: 'Home',
            position: 'left',
            className: 'header-home-link',
            activeBaseRegex: '^((?!modules|api-reference).)*$',
          },
          {
            type: 'docSidebar',
            sidebarId: 'modulesSidebar',
            position: 'left',
            label: 'Modules',
            className: 'header-modules-link',
          },
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Guides',
            className: 'header-guides-link',
          },
          {
            to: '/api-reference',
            label: 'API Reference',
            position: 'left',
            className: 'header-api-link',
          },
          {
            to: 'https://github.com/midil-labs/midil-kit',
            position: 'right',
            target: '_blank',
            className: 'header-github-link',
          },
          {
            to: 'https://discord.gg/midil',
            position: 'right',
            target: '_blank',
            className: 'header-slack-link',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'Introduction',
                to: '/',
              },
              {
                label: 'Getting Started',
                to: '/getting-started',
              },
              {
                label: 'Authentication',
                to: '/auth/overview',
              },
              {
                label: 'Event System',
                to: '/modules/event',
              },
              {
                label: 'HTTP Client',
                to: '/modules/http',
              },
            ],
          },
          {
            title: 'Core Modules',
            items: [
              {
                label: 'Authentication & Authorization',
                to: '/modules/auth',
              },
              {
                label: 'Event System',
                to: '/modules/event',
              },
              {
                label: 'HTTP Client',
                to: '/modules/http',
              },
              {
                label: 'JSON:API',
                to: '/modules/jsonapi',
              },
              {
                label: 'FastAPI Extensions',
                to: '/modules/extensions',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/midil-labs/midil-kit',
              },
              {
                label: 'GitHub Issues',
                href: 'https://github.com/midil-labs/midil-kit/issues',
              },
              {
                label: 'GitHub Discussions',
                href: 'https://github.com/midil-labs/midil-kit/discussions',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'PyPI Package',
                href: 'https://pypi.org/project/midil-kit/',
              },
              {
                label: 'Changelog',
                href: 'https://github.com/midil-labs/midil-kit/blob/main/CHANGELOG.md',
              },
              {
                label: 'Midil.io',
                href: 'https://midil.io',
              },
              {
                label: 'License',
                href: 'https://github.com/midil-labs/midil-kit/blob/main/LICENSE',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Midil.io. Built with ❤️ by the Midil team.`,
      },
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 6,
      },
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      announcementBar: {
        id: 'midil_ctas',
        content: '🚀 <strong>Midil Kit v1.0</strong> is now available! <a href="/getting-started">Get started</a> or <a href="https://github.com/midil-labs/midil-kit">view on GitHub</a>',
        backgroundColor: '#000000',
        textColor: '#FFFFFF',
        isCloseable: true,
      },
      zoom: {
        selector: '.markdown img:not(.not-zoom)',
        background: {
          light: 'rgb(255, 255, 255)',
          dark: 'rgb(50, 50, 50)',
        },
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: [
          'python',
          'bash',
          'json',
          'yaml',
          'toml',
          'ini',
          'docker',
          'nginx',
          'sql',
          'graphql',
        ],
      },
      liveCodeBlock: {
        /**
         * The position of the live playground, above or under the editor
         * Possible values: "top" | "bottom"
         */
        playgroundPosition: 'bottom',
      },
    }),

  themes: [
    '@docusaurus/theme-mermaid',
    'docusaurus-theme-openapi-docs', // OpenAPI theme
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        indexBlog: false,
        indexDocs: true,
        docsRouteBasePath: '/',
        hashed: true,
        explicitSearchResultPath: true,
        searchBarPosition: 'right',
        searchBarShortcutHint: true,
      },
    ],
  ],

  plugins: [
    require.resolve('docusaurus-plugin-image-zoom'),
    '@docusaurus/theme-live-codeblock',
    [
      '@docusaurus/plugin-client-redirects',
      {
        createRedirects(existingPath) {
          // Add custom redirects here as needed
          // Example: if you move /old-path to /new-path
          if (!existingPath.includes('/docs') && existingPath !== '/') {
            return [existingPath.replace('/', '/docs/', 1)];
          }
          return undefined;
        },
      },
    ],
    [
      'docusaurus-plugin-openapi-docs',
      {
        id: 'api',
        docsPluginId: 'classic',
        config: {
          midilkit: {
            // You can either:
            // 1. Point to a local OpenAPI spec file
            specPath: './static/openapi.yaml',
            // 2. Or fetch from a URL
            // specPath: 'https://api.midil.io/openapi.yaml',
            outputDir: 'docs/api-reference',
            sidebarOptions: {
              groupPathsBy: 'tag',
              categoryLinkSource: 'tag',
            },
            baseUrl: '/api-reference/',
          },
        }
      },
    ],
    [
      '@docusaurus/plugin-ideal-image',
      {
        quality: 70,
        max: 1000,
        min: 300,
        steps: 7,
        disableInDev: false,
      },
    ],
  ],
};

module.exports = config;
