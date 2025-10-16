/**
 * Creating a sidebar enables you to:
 * - create an ordered group of docs
 * - render a sidebar for each doc of that group
 * - provide next/previous navigation
 *
 * The sidebars can be generated from the filesystem, or explicitly defined here.
 *
 * Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // Main tutorial/guide sidebar
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'introduction',
      label: '🏠 Introduction',
    },
    {
      type: 'doc',
      id: 'getting-started',
      label: '🚀 Getting Started',
    },
    {
      type: 'category',
      label: '📖 Core Guides',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: '🔐 Authentication',
          items: [
            'auth/overview',
            // 'auth/cognito',
            // 'auth/interfaces',
          ],
        },
        // Future guide categories to add:
        // {
        //   type: 'category',
        //   label: '📡 Event System',
        //   items: [
        //     'event/overview',
        //     'event/consumer',
        //     'event/producer',
        //     'event/scheduler',
        //   ],
        // },
        // {
        //   type: 'category',
        //   label: '🌐 HTTP Client',
        //   items: [
        //     'http/overview',
        //     'http/client',
        //     'http/overrides',
        //   ],
        // },
        // {
        //   type: 'category',
        //   label: '🚀 FastAPI Extensions',
        //   items: [
        //     'midilapi/overview',
        //     'midilapi/config',
        //     'midilapi/dependencies',
        //   ],
        // },
      ],
    },
  ],

  // Modules sidebar - mirrors the codebase structure
  modulesSidebar: [
    {
      type: 'html',
      value: '<div class="sidebar-title">Core Modules</div>',
      defaultStyle: true,
    },
    {
      type: 'category',
      label: '🔐 Authentication (midil.auth)',
      collapsed: false,
      items: [
        'modules/auth',
        // Future: Add sub-pages
        // 'modules/auth/interfaces',
        // 'modules/auth/cognito',
        // 'modules/auth/exceptions',
      ],
    },
    {
      type: 'category',
      label: '📡 Event System (midil.event)',
      collapsed: false,
      items: [
        'modules/event',
        // Future: Add sub-pages
        // 'modules/event/event-bus',
        // 'modules/event/producers',
        // 'modules/event/consumers',
        // 'modules/event/context',
      ],
    },
    {
      type: 'category',
      label: '🌐 HTTP Client (midil.http_client)',
      collapsed: false,
      items: [
        'modules/http',
        // Future: Add sub-pages
        // 'modules/http/client',
        // 'modules/http/retry',
        // 'modules/http/transport',
      ],
    },
    {
      type: 'category',
      label: '🚀 FastAPI Extensions (midil.midilapi)',
      collapsed: false,
      items: [
        'modules/extensions',
        // Future: Add sub-pages
        // 'modules/extensions/middleware',
        // 'modules/extensions/dependencies',
        // 'modules/extensions/responses',
      ],
    },
    // Future modules to add:
    // {
    //   type: 'category',
    //   label: '📋 JSON:API (midil.jsonapi)',
    //   collapsed: false,
    //   items: [
    //     'modules/jsonapi',
    //     'modules/jsonapi/document',
    //     'modules/jsonapi/query',
    //     'modules/jsonapi/config',
    //     'modules/jsonapi/mixins',
    //   ],
    // },
    // {
    //   type: 'category',
    //   label: '📝 Logger (midil.logger)',
    //   collapsed: false,
    //   items: [
    //     'modules/logger',
    //     'modules/logger/factory',
    //     'modules/logger/config',
    //     'modules/logger/handlers',
    //     'modules/logger/sensitive',
    //     'modules/logger/setup',
    //     'modules/logger/utils',
    //   ],
    // },
    // {
    //   type: 'category',
    //   label: '🛠️ Utilities (midil.utils)',
    //   collapsed: false,
    //   items: [
    //     'modules/utils',
    //     'modules/utils/async_iterators',
    //     'modules/utils/backoff',
    //     'modules/utils/misc',
    //     'modules/utils/models',
    //     'modules/utils/retry',
    //     'modules/utils/time',
    //   ],
    // },
  ],
};

module.exports = sidebars;
