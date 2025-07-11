import { lazy } from 'react';
import {
  UploadOutlined,
  TeamOutlined,
  SettingOutlined,
  DatabaseOutlined,
  ApiOutlined,
} from '@ant-design/icons';

// --- DEFINE YOUR LAZY COMPONENTS ONCE AT THE TOP ---

const Uploads = lazy(() => import(
  /* webpackPrefetch: true */
  /* vite-prefetch */
  '../pages/Uploads'
  ));

const Editor = lazy(() => import(
  /* webpackPrefetch: true */
  /* vite-prefetch */
  '../pages/Editor'
  ));

// Now, your configuration array is incredibly clean and readable.
export const appConfig = [
  {
    key: '/uploads',
    path: '/uploads',
    component: Uploads, // <-- Reuse the variable
    label: 'Uploads (L1)',
    icon: <UploadOutlined />,
    type: 'item',
  },
  {
    key: 'management',
    label: 'Management (L1)',
    icon: <TeamOutlined />,
    type: 'group',
    children: [
      {
        key: '/management/editor',
        path: '/management/editor',
        component: Editor, // <-- Reuse the variable
        label: 'Editor (L2)',
        type: 'item',
      },
      {
        key: 'settings-group',
        label: 'Settings (L2)',
        icon: <SettingOutlined />,
        type: 'group',
        children: [
          {
            key: '/management/settings/database',
            path: '/management/settings/database',
            component: Uploads, // <-- Reuse the variable again
            label: 'Database (L3)',
            icon: <DatabaseOutlined />,
            type: 'item',
          },
          {
            key: '/management/settings/api-keys',
            path: '/management/settings/api-keys',
            component: Editor, // <-- And again
            label: 'API Keys (L3)',
            icon: <ApiOutlined />,
            type: 'item',
          },
        ],
      },
    ],
  },
];