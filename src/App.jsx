import { Switch, Route, Redirect } from "react-router-dom";
import "antd/dist/antd.css";
import "./assets/styles/main.css";
import "./assets/styles/responsive.css";
import "./assets/styles/CustomCalendar.css"
import { appConfig } from './config/appConfig.jsx';
import MainLayout from '../src/components/MainLayout.jsx';
import { Suspense } from 'react';

// A simple loading component. You can make this a fancy spinner.
const LoadingFallback = () => (
  <div style={{ textAlign: 'center', padding: '50px' }}>
    Loading...
  </div>
);

const generateRoutes = (config) => {
  let routes = [];

  for (const item of config) {
    // If the item has a component, create a route for it.
    if (item.component) {
      routes.push(
        <Route
          key={item.key}
          exact
          path={item.path}
          component={item.component}
        />
      );
    }
    // If the item has children, recurse to generate their routes as well.
    if (item.children) {
      routes = routes.concat(generateRoutes(item.children));
    }
  }

  return routes;
};

function App() {
  return (
    <div className="App">
      <MainLayout>
        {/* 2. Wrap your Switch with Suspense */}
        <Suspense fallback={<LoadingFallback />}>
          <Switch>
            {generateRoutes(appConfig)}
            <Redirect from="*" to={appConfig[0].path} />
          </Switch>
        </Suspense>
      </MainLayout>
    </div>
  );
}

export default App;
