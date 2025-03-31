import { createRouter, createWebHistory } from 'vue-router';
import ComparisonPage from './components/ComparisonPage.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/comparison/task/sztaxi',  // 默认重定向到invoice任务
    meta: {
      title: 'DocuSpotlight - 首页'
    }
  },
  {
    path: '/comparison/task/idd',
    name: 'DefaultComparison',
    component: ComparisonPage,
    props: {
      taskId: 'idd'
    },
    meta: {
      title: 'DocuSpotlight - 演示'
    }
  },
  {
    path: '/comparison/task/:taskId',
    name: 'ComparisonTask',
    component: () => import('./components/ComparisonPage.vue'),
    props: true
  }
];

// 路由前置守卫，设置页面标题
const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = to.meta.title;
  }
  next();
});

export default router;