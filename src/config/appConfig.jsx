import { lazy } from 'react';
import {
  AppstoreOutlined,
  BookOutlined,
  TeamOutlined,
  SettingOutlined,
  DatabaseOutlined,
  ApiOutlined,
  CodeOutlined,
} from '@ant-design/icons';

// --- DEFINE YOUR LAZY COMPONENTS ONCE AT THE TOP ---

const Dashboard = lazy(() => import('../pages/Dashboard'));
const Journal = lazy(() => import('../pages/Journal'));
const EditorDemo = lazy(() => import('../pages/Editor')); // Renamed for clarity
const YoutubeDemo = lazy(() => import('../pages/youtube-transcription/YouTubeTranscriptPro'));

// Now, your configuration array is incredibly clean and readable.
export const appConfig = [
  {
    key: '/dashboard',
    path: '/dashboard',
    component: Dashboard,
    label: 'Dashboard',
    icon: <AppstoreOutlined />,
    type: 'item',
  },
  {
    key: '/journal',
    path: '/journal',
    component: Journal,
    label: 'Journal',
    icon: <BookOutlined />,
    type: 'item',
  },
  {
    key: 'stt',
    label: 'Speech To Text',
    icon: <TeamOutlined />,
    type: 'group',
    children: [
      {
        key: '/management/editor-demo',
        path: '/management/editor-demo',
        component: YoutubeDemo,
        label: 'YouTube',
        icon: <CodeOutlined />,
        type: 'item',
      }
      ]
  },
  {
    key: 'management',
    label: 'Management',
    icon: <TeamOutlined />,
    type: 'group',
    children: [
      {
        key: '/management/editor-demo',
        path: '/management/editor-demo',
        component: EditorDemo,
        label: 'Editor Demo',
        icon: <CodeOutlined />,
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
            component: Dashboard, // Example: re-using a component
            label: 'Database (L3)',
            icon: <DatabaseOutlined />,
            type: 'item',
          },
          {
            key: '/management/settings/api-keys',
            path: '/management/settings/api-keys',
            component: EditorDemo, // Example: re-using a component
            label: 'API Keys (L3)',
            icon: <ApiOutlined />,
            type: 'item',
          },
        ],
      },
    ],
  },
];