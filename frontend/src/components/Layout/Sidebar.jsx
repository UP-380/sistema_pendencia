import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Sidebar.css';

const VERSAO_SISTEMA = '1.0.0';

// Componente simples para exibir informações do usuário ou Avatar
const UserProfile = ({ user }) => {
  if (!user) return null;

  return (
    <div className="sidebar-user-info">
      <div className="user-avatar">
        {user.nome ? user.nome.charAt(0).toUpperCase() : '?'}
      </div>
      <div className="user-details">
        <span className="user-name">{user.nome || user.email}</span>
        <span className="user-role">
          {user.tipo === 'adm' ? 'Administrador' :
            user.tipo === 'supervisor' ? 'Supervisor' :
              user.tipo === 'operador' ? 'Operador' : 'Usuário'}
        </span>
      </div>
    </div>
  );
};

const Sidebar = () => {
  const location = useLocation();
  const { user } = useAuth();

  // Controle de permissões baseado no tipo do usuário
  const canAccessRoute = (path) => {
    if (!user) return false;
    const tipo = user.tipo;

    // Rotas públicas ou básicas
    if (['/dashboard', '/empresas', '/segmentos', '/painel-colaborador'].includes(path)) return true;

    const regras = {
      '/importar-planilha': ['adm', 'operador'],
      '/nova-pendencia': ['adm', 'operador', 'supervisor'],
      '/pendencias': ['adm', 'operador', 'supervisor'],
      '/pendencias-resolvidas': ['adm', 'operador', 'supervisor'],
      '/operador': ['adm', 'operador', 'supervisor'],
      '/supervisor': ['adm', 'supervisor'],
      '/relatorio-mensal': ['adm', 'supervisor', 'operador', 'cliente_supervisor'],
      '/historico-importacoes': ['adm'],
      '/logs-recentes': ['adm'],
      '/gerenciar/usuarios': ['adm'],
      '/gerenciar/segmentos': ['adm'],
      '/gerenciar/empresas': ['adm'],
      '/base-conhecimento': [] // Placeholder se existir futuramente
    };

    // Verifica se a rota começa com alguma das chaves (para sub-rotas) ou é exata
    const ruleKey = Object.keys(regras).find(key => path.startsWith(key));
    if (ruleKey) {
      return regras[ruleKey].includes(tipo);
    }

    return true; // Se não tem regra explícita, assume permitido (ou ajuste conforme segurança)
  };

  const isAdmin = user?.tipo === 'adm';

  const [relatoriosExpanded, setRelatoriosExpanded] = useState(false);
  const [cadastrosExpanded, setCadastrosExpanded] = useState(false);
  const [operacionalExpanded, setOperacionalExpanded] = useState(false);
  const [adminExpanded, setAdminExpanded] = useState(false);

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth <= 768;
    }
    return false;
  });
  const [isOpening, setIsOpening] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const touchStartTime = useRef(0);

  const isActive = (path) => {
    // Exact match for root-like paths, startsWith for others
    if (path === '/') return location.pathname === '/';
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const isOperacionalActive = () => {
    return isActive('/nova-pendencia') || isActive('/importar-planilha') || isActive('/operador') || isActive('/supervisor');
  };

  const isRelatoriosActive = () => {
    return isActive('/relatorio-mensal') || isActive('/historico-importacoes') || isActive('/logs-recentes') || isActive('/pendencias-resolvidas');
  };

  const isAdminActive = () => {
    return location.pathname.startsWith('/gerenciar');
  };

  // Expandir menus automaticamente
  useEffect(() => {
    if (isRelatoriosActive()) setRelatoriosExpanded(true);
    if (isOperacionalActive()) setOperacionalExpanded(true);
    if (isAdminActive()) setAdminExpanded(true);
  }, [location.pathname]);

  // Responsividade
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (!mobile) setIsMobileMenuOpen(false);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fechar menu mobile ao navegar
  const prevPathname = useRef(location.pathname);
  const menuOpenTime = useRef(0);

  useEffect(() => {
    if (prevPathname.current === location.pathname) return;

    const timeSinceOpen = Date.now() - menuOpenTime.current;
    if (timeSinceOpen < 800) {
      prevPathname.current = location.pathname;
      return;
    }

    if (isMobile && isMobileMenuOpen) {
      prevPathname.current = location.pathname;
      const timer = setTimeout(() => {
        setShowOverlay(false);
        setIsMobileMenuOpen(false);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      prevPathname.current = location.pathname;
    }
  }, [location.pathname, isMobile, isMobileMenuOpen]);

  const toggleRelatorios = (e) => { e.preventDefault(); setRelatoriosExpanded(!relatoriosExpanded); };
  const toggleOperacional = (e) => { e.preventDefault(); setOperacionalExpanded(!operacionalExpanded); };
  const toggleAdmin = (e) => { e.preventDefault(); setAdminExpanded(!adminExpanded); };

  // Definição dos itens do menu principal
  const menuItems = useMemo(() => {
    return [
      { path: '/dashboard', icon: 'fa-chart-line', label: 'Dashboard', title: 'Dashboard' },
      { path: '/empresas', icon: 'fa-building', label: 'Empresas', title: 'Empresas' },
      { path: '/segmentos', icon: 'fa-layer-group', label: 'Segmentos', title: 'Segmentos' }
    ].filter(item => canAccessRoute(item.path));
  }, [user]); // user changed dependency

  const operacionalSubItems = useMemo(() => {
    return [
      { path: '/pendencias', icon: 'fa-list', label: 'Todas Pendências', title: 'Lista de Pendências' },
      { path: '/nova-pendencia', icon: 'fa-plus-circle', label: 'Nova Pendência', title: 'Nova Pendência' },
      { path: '/importar-planilha', icon: 'fa-file-import', label: 'Importar', title: 'Importar Planilha' },
      { path: '/operador', icon: 'fa-user-cog', label: 'Operador', title: 'Painel Operador' },
      { path: '/supervisor', icon: 'fa-user-check', label: 'Supervisor', title: 'Painel Supervisor' }
    ].filter(item => canAccessRoute(item.path));
  }, [user]);

  const relatoriosSubItems = useMemo(() => {
    return [
      { path: '/relatorio-mensal', icon: 'fa-file-alt', label: 'Relatório Mensal', title: 'Relatório Mensal' },
      { path: '/pendencias-resolvidas', icon: 'fa-check-double', label: 'Resolvidas', title: 'Pendências Resolvidas' },
      { path: '/historico-importacoes', icon: 'fa-history', label: 'Histórico', title: 'Histórico de Importações' },
      { path: '/logs-recentes', icon: 'fa-clipboard-list', label: 'Logs', title: 'Logs do Sistema' }
    ].filter(item => canAccessRoute(item.path));
  }, [user]);

  const adminSubItems = useMemo(() => {
    if (!isAdmin) return [];
    return [
      { path: '/gerenciar/usuarios', icon: 'fa-users-cog', label: 'Usuários', title: 'Gerenciar Usuários' },
      { path: '/gerenciar/segmentos', icon: 'fa-th-large', label: 'Segm. Admin', title: 'Gerenciar Segmentos' },
      { path: '/gerenciar/empresas', icon: 'fa-city', label: 'Empresas Admin', title: 'Gerenciar Empresas' }
    ];
  }, [isAdmin]);

  if (!user) return null;

  return (
    <>
      <button
        className="mobile-menu-toggle"
        onTouchStart={() => { touchStartTime.current = Date.now(); }}
        onTouchEnd={(e) => {
          if (Date.now() - touchStartTime.current < 300) {
            e.preventDefault(); e.stopPropagation();
            const newState = !isMobileMenuOpen;
            setIsMobileMenuOpen(newState);
            if (newState) {
              setIsOpening(true);
              menuOpenTime.current = Date.now();
              setTimeout(() => { setShowOverlay(true); setTimeout(() => setIsOpening(false), 200); }, 150);
            } else {
              setShowOverlay(false);
              menuOpenTime.current = 0;
            }
          }
        }}
        onClick={(e) => {
          if (Date.now() - touchStartTime.current > 300) {
            e.preventDefault(); e.stopPropagation();
            const newState = !isMobileMenuOpen;
            setIsMobileMenuOpen(newState);
            if (newState) {
              setIsOpening(true);
              menuOpenTime.current = Date.now();
              setTimeout(() => { setShowOverlay(true); setTimeout(() => setIsOpening(false), 200); }, 100);
            } else {
              setShowOverlay(false);
              menuOpenTime.current = 0;
            }
          }
        }}
      >
        <i className={`fas ${isMobileMenuOpen ? 'fa-times' : 'fa-bars'}`}></i>
      </button>

      {isMobileMenuOpen && showOverlay && (
        <div className="sidebar-overlay show" onClick={() => { if (!isOpening) { setShowOverlay(false); setIsMobileMenuOpen(false); } }}></div>
      )}

      <nav className={`sidebar ${isMobile ? (isMobileMenuOpen ? 'mobile-open' : '') : ''}`} id="sidebar">

        <div className="sidebar-header">
          <i className="fas fa-cubes sidebar-logo-icon"></i>
          <div className="sidebar-text" style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#0e3b6f' }}>
            UP380
          </div>
        </div>

        <div className="sidebar-content">
          <div className="sidebar-menu-wrapper">
            <div style={{ padding: '0 10px' }}><UserProfile user={user} /></div>
            <div className="sidebar-divider"></div>

            {menuItems.map(item => (
              <Link key={item.path} to={item.path} className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`} title={item.title}>
                <i className={`fas ${item.icon}`}></i>
                <span className="sidebar-text">{item.label}</span>
              </Link>
            ))}

            {operacionalSubItems.length > 0 && (
              <div className="sidebar-menu-group">
                <button type="button" className={`sidebar-item sidebar-menu-toggle ${isOperacionalActive() ? 'active' : ''}`} onClick={toggleOperacional}>
                  <i className="fas fa-briefcase"></i>
                  <span className="sidebar-text">Operacional</span>
                  <i className={`fas fa-chevron-right sidebar-chevron ${operacionalExpanded ? 'expanded' : ''}`}></i>
                </button>
                <div className={`sidebar-submenu ${operacionalExpanded ? 'open' : ''}`}>
                  {operacionalSubItems.map(subItem => (
                    <Link key={subItem.path} to={subItem.path} className={`sidebar-item sidebar-submenu-item ${isActive(subItem.path) ? 'active' : ''}`}>
                      <i className={`fas ${subItem.icon}`}></i>
                      <span className="sidebar-text">{subItem.label}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {relatoriosSubItems.length > 0 && (
              <div className="sidebar-menu-group">
                <button type="button" className={`sidebar-item sidebar-menu-toggle ${isRelatoriosActive() ? 'active' : ''}`} onClick={toggleRelatorios}>
                  <i className="fas fa-chart-pie"></i>
                  <span className="sidebar-text">Relatórios</span>
                  <i className={`fas fa-chevron-right sidebar-chevron ${relatoriosExpanded ? 'expanded' : ''}`}></i>
                </button>
                <div className={`sidebar-submenu ${relatoriosExpanded ? 'open' : ''}`}>
                  {relatoriosSubItems.map(subItem => (
                    <Link key={subItem.path} to={subItem.path} className={`sidebar-item sidebar-submenu-item ${isActive(subItem.path) ? 'active' : ''}`}>
                      <i className={`fas ${subItem.icon}`}></i>
                      <span className="sidebar-text">{subItem.label}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {adminSubItems.length > 0 && (
              <div className="sidebar-menu-group">
                <button type="button" className={`sidebar-item sidebar-menu-toggle ${isAdminActive() ? 'active' : ''}`} onClick={toggleAdmin}>
                  <i className="fas fa-cogs"></i>
                  <span className="sidebar-text">Administração</span>
                  <i className={`fas fa-chevron-right sidebar-chevron ${adminExpanded ? 'expanded' : ''}`}></i>
                </button>
                <div className={`sidebar-submenu ${adminExpanded ? 'open' : ''}`}>
                  {adminSubItems.map(subItem => (
                    <Link key={subItem.path} to={subItem.path} className={`sidebar-item sidebar-submenu-item ${isActive(subItem.path) ? 'active' : ''}`}>
                      <i className={`fas ${subItem.icon}`}></i>
                      <span className="sidebar-text">{subItem.label}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

          </div>

          <div className="sidebar-footer">
            <div className="sidebar-footer-content">
              <div className="sidebar-footer-meta" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', fontSize: '0.7rem', color: '#9ca3af' }}>
                <span>v{VERSAO_SISTEMA}</span>
                <span className="sidebar-text">UP Gestão Inteligente</span>
              </div>
            </div>
          </div>
        </div>
      </nav>
    </>
  );
};

export default Sidebar;
